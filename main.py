"""
Главный файл приложения SaveConfe
Точка входа в приложение
"""
import sys
import logging
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

from ui.main_window import MainWindow
from ui.login_window import LoginWindow
from core.database import init_db, Database
from core.auth import AuthManager
from core.admin_check import require_admin, is_admin

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('saveconfe.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def setup_application():
    """Настройка приложения"""
    app = QApplication(sys.argv)
    app.setApplicationName("SaveConfe")
    app.setOrganizationName("SaveConfe")
    
    # Загрузка стилей
    styles_path = Path("resources/styles.qss")
    if styles_path.exists():
        with open(styles_path, 'r', encoding='utf-8') as f:
            app.setStyleSheet(f.read())
    else:
        logger.warning("Файл стилей не найден")
    
    return app


def main():
    """Главная функция"""
    try:
        # Проверка и запрос прав администратора
        # Важно: это должно быть ДО создания QApplication
        if not require_admin():
            logger.info("Приложение не запущено с правами администратора. Выход.")
            return 1
        
        # Проверяем еще раз (на случай если был перезапуск)
        if not is_admin():
            logger.error("Не удалось получить права администратора")
            # Попробуем показать сообщение через консоль, так как QApplication еще не создан
            print("ОШИБКА: Для работы SaveConfe требуются права администратора.")
            print("Запустите приложение от имени администратора.")
            return 1
        
        # Инициализация базы данных
        logger.info("Инициализация базы данных...")
        if not init_db():
            logger.error("Не удалось инициализировать базу данных")
            return 1
        
        # Создание приложения
        app = setup_application()
        
        # Создание менеджера авторизации
        auth = AuthManager()
        
        # Показываем окно входа
        login_window = LoginWindow(auth)
        if login_window.exec() != LoginWindow.DialogCode.Accepted:
            logger.info("Вход отменён пользователем")
            return 0
        
        # Проверяем, что авторизация прошла успешно
        if not auth.is_authenticated():
            logger.error("Авторизация не прошла")
            QMessageBox.warning(None, "Ошибка", "Ошибка авторизации. Приложение будет закрыто.")
            return 1
        
        # Создание главного окна с передачей авторизованного менеджера
        main_window = MainWindow(auth_manager=auth)
        main_window.show()
        
        logger.info("Приложение запущено с правами администратора")
        
        # Запуск приложения
        return app.exec()
    
    except Exception as e:
        logger.critical(f"Критическая ошибка: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())

