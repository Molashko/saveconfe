"""
Окно входа в систему
"""
import logging
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QMessageBox)
from PyQt6.QtCore import Qt

from core.auth import AuthManager

logger = logging.getLogger(__name__)


class LoginWindow(QDialog):
    """Окно авторизации"""
    
    def __init__(self, auth_manager: AuthManager, parent=None):
        super().__init__(parent)
        self.auth = auth_manager
        self.setWindowTitle("Вход в систему")
        self.setFixedSize(450, 320)
        self.setModal(True)
        
        self._create_ui()
        
        # Проверяем, есть ли администратор
        self._check_admin_exists()
    
    def _create_ui(self):
        """Создание интерфейса"""
        # Устанавливаем светлый фон для лучшей видимости
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f5f5;
            }
            QLabel {
                color: #212121;
                font-size: 12px;
                font-weight: bold;
            }
            QLineEdit {
                background-color: white;
                border: 2px solid #ddd;
                border-radius: 4px;
                padding: 8px;
                font-size: 12px;
                color: #212121;
            }
            QLineEdit:focus {
                border: 2px solid #2196F3;
            }
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px 20px;
                font-size: 12px;
                font-weight: bold;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(40, 0, 40, 40)
        
        # Заголовок
        title = QLabel("SaveConfe")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #1976D2; padding: 5px 15px 0px 15px;")
        layout.addWidget(title)
        
        # Поле имени пользователя (без отступа, сразу после заголовка)
        
        # Поле имени пользователя
        username_layout = QVBoxLayout()
        username_layout.setSpacing(6)
        username_label = QLabel("Имя пользователя:")
        username_label.setStyleSheet("color: #212121; font-size: 14px; font-weight: bold;")
        username_layout.addWidget(username_label)
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("admin")
        self.username_edit.setStyleSheet("""
            QLineEdit {
                background-color: white;
                border: 2px solid #ddd;
                border-radius: 4px;
                padding: 12px;
                font-size: 14px;
                color: #212121;
                min-height: 20px;
            }
            QLineEdit:focus {
                border: 2px solid #2196F3;
            }
        """)
        username_layout.addWidget(self.username_edit)
        layout.addLayout(username_layout)
        
        # Поле пароля
        password_layout = QVBoxLayout()
        password_layout.setSpacing(8)
        password_label = QLabel("Пароль:")
        password_label.setStyleSheet("color: #212121; font-size: 14px; font-weight: bold;")
        password_layout.addWidget(password_label)
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.setPlaceholderText("Введите пароль")
        self.password_edit.setStyleSheet("""
            QLineEdit {
                background-color: white;
                border: 2px solid #ddd;
                border-radius: 4px;
                padding: 12px;
                font-size: 14px;
                color: #212121;
                min-height: 20px;
            }
            QLineEdit:focus {
                border: 2px solid #2196F3;
            }
        """)
        self.password_edit.returnPressed.connect(self._login)
        password_layout.addWidget(self.password_edit)
        layout.addLayout(password_layout)
        
        # Добавляем отступ перед кнопками
        layout.addSpacing(15)
        
        # Кнопки
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(15)
        login_button = QPushButton("Войти")
        login_button.setDefault(True)
        login_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 12px 40px;
                font-size: 14px;
                font-weight: bold;
                min-height: 25px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        login_button.clicked.connect(self._login)
        cancel_button = QPushButton("Отмена")
        cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #757575;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 12px 40px;
                font-size: 14px;
                font-weight: bold;
                min-height: 25px;
            }
            QPushButton:hover {
                background-color: #616161;
            }
            QPushButton:pressed {
                background-color: #424242;
            }
        """)
        cancel_button.clicked.connect(self.reject)
        
        buttons_layout.addWidget(login_button)
        buttons_layout.addWidget(cancel_button)
        layout.addLayout(buttons_layout)
        
        # Добавляем отступ внизу
        layout.addSpacing(10)
        
        # Устанавливаем фокус на поле имени пользователя
        self.username_edit.setFocus()
    
    def _check_admin_exists(self):
        """Проверка существования администратора"""
        try:
            from core.database import Database
            db = Database()
            admin = db.get_user_by_username("admin")
            if not admin:
                # Создаём администратора по умолчанию
                self._create_default_admin()
        except Exception as e:
            logger.error(f"Ошибка проверки администратора: {e}")
    
    def _create_default_admin(self):
        """Создание администратора по умолчанию"""
        reply = QMessageBox.question(
            self,
            "Создание администратора",
            "Администратор не найден. Создать администратора по умолчанию?\n\n"
            "Имя пользователя: admin\n"
            "Пароль: admin\n\n"
            "ВНИМАНИЕ: Смените пароль после первого входа!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.auth.create_admin("admin", "admin")
                QMessageBox.information(
                    self,
                    "Успех",
                    "Администратор создан:\nИмя: admin\nПароль: admin\n\n"
                    "Смените пароль после первого входа!"
                )
                self.username_edit.setText("admin")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось создать администратора: {e}")
    
    def _login(self):
        """Обработка входа"""
        username = self.username_edit.text().strip()
        password = self.password_edit.text()
        
        if not username or not password:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setWindowTitle("Ошибка")
            msg.setText("Введите имя пользователя и пароль")
            msg.setStyleSheet("""
                QMessageBox {
                    background-color: white;
                }
                QMessageBox QLabel {
                    color: #212121;
                    font-size: 13px;
                    font-weight: normal;
                }
                QPushButton {
                    background-color: #2196F3;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 8px 20px;
                    font-size: 12px;
                    font-weight: bold;
                    min-width: 80px;
                }
                QPushButton:hover {
                    background-color: #1976D2;
                }
            """)
            msg.exec()
            return
        
        try:
            if self.auth.login(username, password):
                self.accept()
            else:
                msg = QMessageBox(self)
                msg.setIcon(QMessageBox.Icon.Warning)
                msg.setWindowTitle("Ошибка")
                msg.setText("Неверное имя пользователя или пароль")
                msg.setStyleSheet("""
                    QMessageBox {
                        background-color: white;
                    }
                    QMessageBox QLabel {
                        color: #212121;
                        font-size: 13px;
                        font-weight: normal;
                    }
                    QPushButton {
                        background-color: #2196F3;
                        color: white;
                        border: none;
                        border-radius: 4px;
                        padding: 8px 20px;
                        font-size: 12px;
                        font-weight: bold;
                        min-width: 80px;
                    }
                    QPushButton:hover {
                        background-color: #1976D2;
                    }
                """)
                msg.exec()
                self.password_edit.clear()
                self.password_edit.setFocus()
        except Exception as e:
            logger.error(f"Ошибка при входе: {e}")
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setWindowTitle("Ошибка")
            msg.setText(f"Ошибка подключения к базе данных:\n{str(e)}")
            msg.setStyleSheet("""
                QMessageBox {
                    background-color: white;
                }
                QMessageBox QLabel {
                    color: #212121;
                    font-size: 12px;
                    font-weight: normal;
                }
                QPushButton {
                    background-color: #f44336;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 8px 20px;
                    font-size: 12px;
                    font-weight: bold;
                    min-width: 80px;
                }
                QPushButton:hover {
                    background-color: #d32f2f;
                }
            """)
            msg.exec()

