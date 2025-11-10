"""
Главное окно приложения SaveConfe
"""
import sys
import logging
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QTabWidget, QTableWidget,
                             QTableWidgetItem, QMessageBox, QSystemTrayIcon,
                             QMenu, QApplication, QTimeEdit, QSpinBox, QGroupBox,
                             QLineEdit, QFileDialog, QHeaderView, QInputDialog)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QIcon, QAction

from core.database import Database
from core.blocker import Blocker
from core.scheduler import Scheduler
from core.monitor import Monitor
from core.auth import AuthManager
from core.autostart import AutostartManager
from models.usage_log import ItemType
from datetime import datetime, time
import sys
import os

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Главное окно приложения"""
    
    def __init__(self, auth_manager=None):
        super().__init__()
        self.setWindowTitle("SaveConfe - Родительский контроль")
        self.setGeometry(100, 100, 900, 700)
        
        # Инициализация компонентов
        self.db = Database()
        self.blocker = Blocker()
        self.scheduler = Scheduler()
        self.monitor = Monitor(self.blocker, self.scheduler, self.db)
        # Используем переданный auth_manager или создаём новый
        self.auth = auth_manager if auth_manager else AuthManager()
        self.autostart = AutostartManager()
        
        # Загрузка данных
        self._load_data()
        
        # Создание UI
        self._create_ui()
        self._create_tray_icon()
        
        # Таймер для обновления
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_status)
        self.update_timer.start(5000)  # Обновление каждые 5 секунд
        
        # Обработка закрытия окна
        self.closeEvent = self._on_close_event
    
    def _create_ui(self):
        """Создание интерфейса"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # Статусная панель
        status_layout = QHBoxLayout()
        self.status_label = QLabel("Статус: Отключено")
        self.status_label.setProperty("class", "status disabled")
        self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #f44336;")
        
        self.toggle_button = QPushButton("Включить блокировку")
        self.toggle_button.setProperty("class", "success")
        self.toggle_button.clicked.connect(self._toggle_blocking)
        
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        status_layout.addWidget(self.toggle_button)
        layout.addLayout(status_layout)
        
        # Вкладки
        self.tabs = QTabWidget()
        self._create_main_tab()
        self._create_sites_tab()
        self._create_apps_tab()
        self._create_time_tab()
        self._create_reports_tab()
        self._create_settings_tab()
        
        layout.addWidget(self.tabs)
        
        # Статус бар
        self.statusBar().showMessage("Готово")
    
    def _create_main_tab(self):
        """Создание главной вкладки"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        title = QLabel("Главная панель")
        title.setProperty("class", "title")
        layout.addWidget(title)
        
        info_label = QLabel(
            "SaveConfe - система родительского контроля для Windows.\n\n"
            "Используйте вкладки для настройки правил блокировки."
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        layout.addStretch()
        self.tabs.addTab(tab, "Главная")
    
    def _create_sites_tab(self):
        """Создание вкладки сайтов"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Кнопки управления
        buttons_layout = QHBoxLayout()
        add_button = QPushButton("Добавить сайт")
        add_button.clicked.connect(self._add_site)
        delete_button = QPushButton("Удалить")
        delete_button.setProperty("class", "danger")
        delete_button.clicked.connect(self._delete_site)
        
        buttons_layout.addWidget(add_button)
        buttons_layout.addWidget(delete_button)
        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)
        
        # Таблица сайтов
        self.sites_table = QTableWidget()
        self.sites_table.setColumnCount(4)
        self.sites_table.setHorizontalHeaderLabels(["ID", "URL", "Лимит (мин)", "Расписание"])
        self.sites_table.horizontalHeader().setStretchLastSection(True)
        self.sites_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.sites_table)
        
        self.tabs.addTab(tab, "Сайты")
        self._update_sites_table()
    
    def _create_apps_tab(self):
        """Создание вкладки приложений"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Кнопки управления
        buttons_layout = QHBoxLayout()
        add_button = QPushButton("Добавить приложение")
        add_button.clicked.connect(self._add_app)
        delete_button = QPushButton("Удалить")
        delete_button.setProperty("class", "danger")
        delete_button.clicked.connect(self._delete_app)
        
        buttons_layout.addWidget(add_button)
        buttons_layout.addWidget(delete_button)
        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)
        
        # Таблица приложений
        self.apps_table = QTableWidget()
        self.apps_table.setColumnCount(5)
        self.apps_table.setHorizontalHeaderLabels(["ID", "Название", "Путь", "Лимит (мин)", "Расписание"])
        self.apps_table.horizontalHeader().setStretchLastSection(True)
        self.apps_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.apps_table)
        
        self.tabs.addTab(tab, "Приложения")
        self._update_apps_table()
    
    def _create_time_tab(self):
        """Создание вкладки времени"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        group = QGroupBox("Общий лимит времени")
        group_layout = QVBoxLayout()
        
        time_layout = QHBoxLayout()
        time_layout.addWidget(QLabel("Лимит времени в день (минуты):"))
        self.daily_limit_spin = QSpinBox()
        self.daily_limit_spin.setMinimum(0)
        self.daily_limit_spin.setMaximum(1440)
        self.daily_limit_spin.setValue(120)
        time_layout.addWidget(self.daily_limit_spin)
        time_layout.addStretch()
        group_layout.addLayout(time_layout)
        
        schedule_layout = QHBoxLayout()
        schedule_layout.addWidget(QLabel("Разрешённое время:"))
        self.schedule_start = QTimeEdit()
        self.schedule_start.setTime(time(9, 0))
        self.schedule_end = QTimeEdit()
        self.schedule_end.setTime(time(20, 0))
        schedule_layout.addWidget(self.schedule_start)
        schedule_layout.addWidget(QLabel(" - "))
        schedule_layout.addWidget(self.schedule_end)
        schedule_layout.addStretch()
        group_layout.addLayout(schedule_layout)
        
        save_button = QPushButton("Сохранить настройки")
        save_button.clicked.connect(self._save_time_settings)
        group_layout.addWidget(save_button)
        
        group.setLayout(group_layout)
        layout.addWidget(group)
        layout.addStretch()
        
        self.tabs.addTab(tab, "Время")
    
    def _create_reports_tab(self):
        """Создание вкладки отчётов"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Кнопки
        buttons_layout = QHBoxLayout()
        refresh_button = QPushButton("Обновить")
        refresh_button.clicked.connect(self._update_reports_table)
        export_button = QPushButton("Экспорт в CSV")
        export_button.clicked.connect(self._export_reports)
        
        buttons_layout.addWidget(refresh_button)
        buttons_layout.addWidget(export_button)
        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)
        
        # Таблица отчётов
        self.reports_table = QTableWidget()
        self.reports_table.setColumnCount(5)
        self.reports_table.setHorizontalHeaderLabels(["Тип", "Название", "Начало", "Окончание", "Длительность (мин)"])
        self.reports_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.reports_table)
        
        self.tabs.addTab(tab, "Отчёты")
        self._update_reports_table()
    
    def _create_settings_tab(self):
        """Создание вкладки настроек"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Пароль
        password_group = QGroupBox("Пароль администратора")
        password_layout = QVBoxLayout()
        
        change_password_layout = QHBoxLayout()
        change_password_layout.addWidget(QLabel("Новый пароль:"))
        self.new_password_edit = QLineEdit()
        self.new_password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        change_password_layout.addWidget(self.new_password_edit)
        
        change_password_button = QPushButton("Изменить пароль")
        change_password_button.clicked.connect(self._change_password)
        change_password_layout.addWidget(change_password_button)
        password_layout.addLayout(change_password_layout)
        
        password_group.setLayout(password_layout)
        layout.addWidget(password_group)
        
        # Автозапуск
        autostart_group = QGroupBox("Автозапуск")
        autostart_layout = QVBoxLayout()
        
        self.autostart_checkbox = QLabel()
        self._update_autostart_status()
        
        autostart_buttons = QHBoxLayout()
        enable_autostart_button = QPushButton("Включить автозапуск")
        enable_autostart_button.clicked.connect(self._enable_autostart)
        disable_autostart_button = QPushButton("Отключить автозапуск")
        disable_autostart_button.clicked.connect(self._disable_autostart)
        
        autostart_buttons.addWidget(enable_autostart_button)
        autostart_buttons.addWidget(disable_autostart_button)
        autostart_buttons.addStretch()
        
        autostart_layout.addWidget(self.autostart_checkbox)
        autostart_layout.addLayout(autostart_buttons)
        autostart_group.setLayout(autostart_layout)
        layout.addWidget(autostart_group)
        
        layout.addStretch()
        self.tabs.addTab(tab, "Настройки")
    
    def _create_tray_icon(self):
        """Создание иконки в системном трее"""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        
        self.tray_icon = QSystemTrayIcon(self)
        # Используем стандартную иконку, если нет своей
        self.tray_icon.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_ComputerIcon))
        
        tray_menu = QMenu()
        
        show_action = QAction("Показать", self)
        show_action.triggered.connect(self.show)
        tray_menu.addAction(show_action)
        
        quit_action = QAction("Выход", self)
        quit_action.triggered.connect(QApplication.quit)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self._tray_icon_activated)
        self.tray_icon.show()
    
    def _tray_icon_activated(self, reason):
        """Обработка активации иконки в трее"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show()
    
    def _load_data(self):
        """Загрузка данных из базы"""
        try:
            # Загрузка сайтов
            sites = self.db.get_all_site_rules()
            site_urls = [site.url for site in sites]
            self.blocker.load_blocked_sites(site_urls)
            
            # Загрузка приложений
            apps = self.db.get_all_app_rules()
            app_paths = [app.app_path for app in apps]
            self.blocker.load_blocked_apps(app_paths)
            
            # Загрузка лимитов времени
            for site in sites:
                if site.time_limit > 0:
                    self.scheduler.set_time_limit(site.url, site.time_limit)
                if site.schedule_start and site.schedule_end:
                    self.scheduler.set_schedule(site.url, site.schedule_start, site.schedule_end)
            
            for app in apps:
                if app.time_limit > 0:
                    self.scheduler.set_time_limit(app.app_name, app.time_limit)
                if app.schedule_start and app.schedule_end:
                    self.scheduler.set_schedule(app.app_name, app.schedule_start, app.schedule_end)
        except Exception as e:
            logger.error(f"Ошибка загрузки данных: {e}")
    
    def _toggle_blocking(self):
        """Переключение блокировки"""
        if self.blocker.is_blocking_enabled:
            # Отключаем блокировку
            self.blocker.disable_blocking()
            self.monitor.stop_monitoring()
            self.status_label.setText("Статус: Отключено")
            self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #f44336;")
            self.toggle_button.setText("Включить блокировку")
            self.toggle_button.setProperty("class", "success")
            self.statusBar().showMessage("Блокировка отключена")
        else:
            if not self.auth.is_authenticated():
                QMessageBox.warning(self, "Ошибка", "Требуется авторизация для включения блокировки")
                return
            
            # Включаем блокировку
            self.blocker.enable_blocking()
            
            # Блокируем все сайты из базы данных
            try:
                sites = self.db.get_all_site_rules()
                blocked_count = 0
                failed_count = 0
                
                for site in sites:
                    success = self.blocker.block_site(site.url)
                    if success:
                        blocked_count += 1
                    else:
                        failed_count += 1
                        logger.warning(f"Не удалось заблокировать сайт: {site.url}")
                
                if failed_count > 0:
                    QMessageBox.warning(
                        self,
                        "Предупреждение",
                        f"Блокировка включена.\n\n"
                        f"Заблокировано: {blocked_count} сайтов\n"
                        f"Ошибок: {failed_count}\n\n"
                        "Проверьте права администратора и логи."
                    )
                else:
                    self.statusBar().showMessage(f"Блокировка включена. Заблокировано сайтов: {blocked_count}")
            except Exception as e:
                logger.error(f"Ошибка при блокировке сайтов: {e}", exc_info=True)
                QMessageBox.warning(
                    self,
                    "Предупреждение",
                    f"Блокировка включена, но возникли ошибки при блокировке сайтов:\n{e}"
                )
            
            # Запускаем мониторинг
            self.monitor.start_monitoring()
            self.status_label.setText("Статус: Включено")
            self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #4CAF50;")
            self.toggle_button.setText("Отключить блокировку")
            self.toggle_button.setProperty("class", "danger")
    
    def _update_status(self):
        """Обновление статуса"""
        if self.blocker.is_blocking_enabled:
            killed = self.blocker.kill_blocked_apps()
            if killed > 0:
                self.statusBar().showMessage(f"Завершено {killed} заблокированных процессов", 3000)
                # Показываем уведомление в трее
                if hasattr(self, 'tray_icon'):
                    self.tray_icon.showMessage(
                        "SaveConfe",
                        f"Завершено {killed} заблокированных процессов",
                        QSystemTrayIcon.MessageIcon.Warning,
                        3000
                    )
            
            # Проверка лимитов времени и показ уведомлений
            self._check_time_limits()
    
    def _add_site(self):
        """Добавление сайта"""
        url, ok = QInputDialog.getText(self, "Добавить сайт", "Введите URL сайта:")
        if ok and url:
            try:
                # Добавляем в базу данных
                self.db.add_site_rule(url)
                
                # Блокируем сайт (если блокировка включена)
                if self.blocker.is_blocking_enabled:
                    success = self.blocker.block_site(url)
                    if not success:
                        QMessageBox.warning(
                            self, 
                            "Предупреждение", 
                            f"Сайт {url} добавлен в список, но не заблокирован.\n\n"
                            "Возможные причины:\n"
                            "1. Блокировка не включена\n"
                            "2. Нет прав администратора\n"
                            "3. Ошибка записи в hosts файл"
                        )
                
                # Обновляем список заблокированных сайтов
                self.blocker.load_blocked_sites([site.url for site in self.db.get_all_site_rules()])
                
                self._update_sites_table()
                self.statusBar().showMessage(f"Сайт {url} добавлен")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось добавить сайт: {e}")
                logger.error(f"Ошибка добавления сайта: {e}", exc_info=True)
    
    def _delete_site(self):
        """Удаление сайта"""
        selected = self.sites_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Предупреждение", "Выберите сайт для удаления")
            return
        
        row = selected[0].row()
        rule_id = int(self.sites_table.item(row, 0).text())
        url = self.sites_table.item(row, 1).text()
        
        reply = QMessageBox.question(self, "Подтверждение", f"Удалить сайт {url}?",
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Удаляем из базы данных
                self.db.delete_site_rule(rule_id)
                
                # Разблокируем сайт (удаляем из hosts файла)
                if self.blocker.is_blocking_enabled:
                    success = self.blocker.unblock_site(url)
                    if not success:
                        logger.warning(f"Не удалось удалить сайт {url} из hosts файла")
                
                # Обновляем список заблокированных сайтов
                self.blocker.load_blocked_sites([site.url for site in self.db.get_all_site_rules()])
                
                self._update_sites_table()
                self.statusBar().showMessage(f"Сайт {url} удалён")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось удалить сайт: {e}")
                logger.error(f"Ошибка удаления сайта: {e}", exc_info=True)
    
    def _add_app(self):
        """Добавление приложения"""
        file_path, _ = QFileDialog.getOpenFileName(self, "Выберите приложение", "", "Executable Files (*.exe)")
        if file_path:
            app_name = file_path.split('\\')[-1]
            try:
                self.db.add_app_rule(file_path, app_name)
                self.blocker.block_app(file_path)
                self._update_apps_table()
                self.statusBar().showMessage(f"Приложение {app_name} добавлено")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось добавить приложение: {e}")
    
    def _delete_app(self):
        """Удаление приложения"""
        selected = self.apps_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Предупреждение", "Выберите приложение для удаления")
            return
        
        row = selected[0].row()
        rule_id = int(self.apps_table.item(row, 0).text())
        app_path = self.apps_table.item(row, 2).text()
        
        reply = QMessageBox.question(self, "Подтверждение", f"Удалить приложение?",
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.db.delete_app_rule(rule_id)
                self.blocker.unblock_app(app_path)
                self._update_apps_table()
                self.statusBar().showMessage("Приложение удалено")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось удалить приложение: {e}")
    
    def _save_time_settings(self):
        """Сохранение настроек времени"""
        QMessageBox.information(self, "Информация", "Настройки времени сохранены")
        # Здесь можно добавить сохранение в базу данных
    
    def _update_sites_table(self):
        """Обновление таблицы сайтов"""
        try:
            sites = self.db.get_all_site_rules()
            self.sites_table.setRowCount(len(sites))
            
            for row, site in enumerate(sites):
                self.sites_table.setItem(row, 0, QTableWidgetItem(str(site.id)))
                self.sites_table.setItem(row, 1, QTableWidgetItem(site.url))
                self.sites_table.setItem(row, 2, QTableWidgetItem(str(site.time_limit)))
                schedule = f"{site.schedule_start or '—'} - {site.schedule_end or '—'}"
                self.sites_table.setItem(row, 3, QTableWidgetItem(schedule))
        except Exception as e:
            logger.error(f"Ошибка обновления таблицы сайтов: {e}")
    
    def _update_apps_table(self):
        """Обновление таблицы приложений"""
        try:
            apps = self.db.get_all_app_rules()
            self.apps_table.setRowCount(len(apps))
            
            for row, app in enumerate(apps):
                self.apps_table.setItem(row, 0, QTableWidgetItem(str(app.id)))
                self.apps_table.setItem(row, 1, QTableWidgetItem(app.app_name))
                self.apps_table.setItem(row, 2, QTableWidgetItem(app.app_path))
                self.apps_table.setItem(row, 3, QTableWidgetItem(str(app.time_limit)))
                schedule = f"{app.schedule_start or '—'} - {app.schedule_end or '—'}"
                self.apps_table.setItem(row, 4, QTableWidgetItem(schedule))
        except Exception as e:
            logger.error(f"Ошибка обновления таблицы приложений: {e}")
    
    def _update_reports_table(self):
        """Обновление таблицы отчётов"""
        try:
            logs = self.db.get_usage_logs(limit=100)
            self.reports_table.setRowCount(len(logs))
            
            for row, log in enumerate(logs):
                self.reports_table.setItem(row, 0, QTableWidgetItem(log.item_type.value))
                self.reports_table.setItem(row, 1, QTableWidgetItem(log.item_name))
                self.reports_table.setItem(row, 2, QTableWidgetItem(log.start_time.strftime("%Y-%m-%d %H:%M:%S")))
                end_time_str = log.end_time.strftime("%Y-%m-%d %H:%M:%S") if log.end_time else "—"
                self.reports_table.setItem(row, 3, QTableWidgetItem(end_time_str))
                self.reports_table.setItem(row, 4, QTableWidgetItem(f"{log.duration:.2f}"))
        except Exception as e:
            logger.error(f"Ошибка обновления таблицы отчётов: {e}")
    
    def _export_reports(self):
        """Экспорт отчётов в CSV"""
        try:
            import pandas as pd
            logs = self.db.get_usage_logs(limit=1000)
            
            data = []
            for log in logs:
                data.append({
                    'Тип': log.item_type.value,
                    'Название': log.item_name,
                    'Начало': log.start_time.strftime("%Y-%m-%d %H:%M:%S"),
                    'Окончание': log.end_time.strftime("%Y-%m-%d %H:%M:%S") if log.end_time else "",
                    'Длительность (мин)': log.duration
                })
            
            df = pd.DataFrame(data)
            file_path, _ = QFileDialog.getSaveFileName(self, "Сохранить отчёт", "", "CSV Files (*.csv)")
            if file_path:
                df.to_csv(file_path, index=False, encoding='utf-8-sig')
                QMessageBox.information(self, "Успех", f"Отчёт сохранён в {file_path}")
        except ImportError:
            QMessageBox.warning(self, "Ошибка", "Библиотека pandas не установлена")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось экспортировать отчёт: {e}")
    
    def _change_password(self):
        """Смена пароля"""
        new_password = self.new_password_edit.text()
        if not new_password:
            QMessageBox.warning(self, "Предупреждение", "Введите новый пароль")
            return
        
        if not self.auth.is_authenticated():
            QMessageBox.warning(self, "Ошибка", "Требуется авторизация")
            return
        
        if len(new_password) < 4:
            QMessageBox.warning(self, "Предупреждение", "Пароль должен содержать минимум 4 символа")
            return
        
        username = self.auth.current_user.username
        # Для упрощения используем текущий пароль как старый
        # В реальном приложении нужно запросить старый пароль
        old_password, ok = QInputDialog.getText(self, "Подтверждение", "Введите текущий пароль:", 
                                                QLineEdit.EchoMode.Password)
        if ok and old_password:
            if self.auth.change_password(username, old_password, new_password):
                QMessageBox.information(self, "Успех", "Пароль успешно изменён")
                self.new_password_edit.clear()
            else:
                QMessageBox.warning(self, "Ошибка", "Неверный текущий пароль")
    
    def _update_autostart_status(self):
        """Обновление статуса автозапуска"""
        if self.autostart.is_enabled():
            self.autostart_checkbox.setText("Статус: Автозапуск включён")
            self.autostart_checkbox.setStyleSheet("color: #4CAF50; font-weight: bold;")
        else:
            self.autostart_checkbox.setText("Статус: Автозапуск отключён")
            self.autostart_checkbox.setStyleSheet("color: #f44336; font-weight: bold;")
    
    def _enable_autostart(self):
        """Включение автозапуска"""
        if getattr(sys, 'frozen', False):
            # Если запущено как EXE
            app_path = sys.executable
        else:
            # Если запущено из исходников, используем python.exe с main.py
            main_py = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'main.py')
            app_path = f'{sys.executable} "{os.path.abspath(main_py)}"'
        
        if self.autostart.enable(app_path):
            self._update_autostart_status()
            QMessageBox.information(self, "Успех", "Автозапуск включён")
        else:
            QMessageBox.warning(self, "Ошибка", "Не удалось включить автозапуск")
    
    def _disable_autostart(self):
        """Отключение автозапуска"""
        if self.autostart.disable():
            self._update_autostart_status()
            QMessageBox.information(self, "Успех", "Автозапуск отключён")
        else:
            QMessageBox.warning(self, "Ошибка", "Не удалось отключить автозапуск")
    
    def _check_time_limits(self):
        """Проверка лимитов времени и показ уведомлений"""
        try:
            # Проверяем активные процессы
            for app_path, proc_info in self.monitor.active_processes.items():
                app_name = proc_info['name']
                remaining = self.scheduler.get_remaining_time(app_name)
                
                if remaining is not None:
                    # Показываем предупреждение за 10 минут до окончания
                    if 0 < remaining <= 10:
                        if hasattr(self, 'tray_icon'):
                            self.tray_icon.showMessage(
                                "SaveConfe",
                                f"Осталось {remaining:.0f} минут для {app_name}",
                                QSystemTrayIcon.MessageIcon.Warning,
                                5000
                            )
        except Exception as e:
            logger.error(f"Ошибка проверки лимитов времени: {e}")
    
    def _on_close_event(self, event):
        """Обработка закрытия окна"""
        if hasattr(self, 'tray_icon') and self.tray_icon.isVisible():
            self.hide()
            event.ignore()
            self.tray_icon.showMessage(
                "SaveConfe",
                "Приложение продолжает работать в фоновом режиме",
                QSystemTrayIcon.MessageIcon.Information,
                2000
            )
        else:
            event.accept()

