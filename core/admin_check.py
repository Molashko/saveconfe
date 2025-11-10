"""
Модуль для проверки и получения прав администратора
"""
import sys
import ctypes
import os
import subprocess
import logging

logger = logging.getLogger(__name__)


def is_admin():
    """
    Проверка, запущено ли приложение с правами администратора
    
    Returns:
        bool: True если запущено с правами администратора
    """
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False


def restart_as_admin():
    """
    Перезапуск приложения с правами администратора
    
    Returns:
        bool: True если перезапуск выполнен, False если пользователь отклонил
    """
    try:
        if is_admin():
            # Уже запущено с правами администратора
            return True
        
        # Перезапускаем с правами администратора
        if sys.argv[0].endswith('.py'):
            # Запуск из исходников (Python скрипт)
            script = os.path.abspath(sys.argv[0])
            python_exe = sys.executable
            # Используем ShellExecute для запроса прав администратора
            ctypes.windll.shell32.ShellExecuteW(
                None,
                "runas",  # Запрос прав администратора
                python_exe,
                f'"{script}"',
                None,
                1  # SW_SHOWNORMAL
            )
        else:
            # Запуск из EXE файла
            exe = os.path.abspath(sys.argv[0])
            ctypes.windll.shell32.ShellExecuteW(
                None,
                "runas",  # Запрос прав администратора
                exe,
                " ".join(f'"{arg}"' for arg in sys.argv[1:]),
                None,
                1  # SW_SHOWNORMAL
            )
        
        logger.info("Запрос прав администратора отправлен")
        return True
    except Exception as e:
        logger.error(f"Ошибка при запросе прав администратора: {e}")
        return False


def require_admin():
    """
    Требовать права администратора. Если их нет, перезапускает приложение.
    
    Returns:
        bool: True если права администратора есть или запрос выполнен, False если отменено
    """
    if is_admin():
        logger.info("Приложение запущено с правами администратора")
        return True
    else:
        logger.warning("Приложение запущено без прав администратора. Запрос прав...")
        
        # Показываем сообщение пользователю через Windows API
        try:
            # Используем MB_YESNO (0x04) и MB_ICONQUESTION (0x20)
            response = ctypes.windll.user32.MessageBoxW(
                None,
                "Для работы SaveConfe требуются права администратора.\n\n"
                "Приложение будет перезапущено с правами администратора.\n\n"
                "Нажмите 'Да' для продолжения или 'Нет' для выхода.",
                "Требуются права администратора",
                0x04 | 0x20  # MB_YESNO | MB_ICONQUESTION
            )
            
            # IDYES = 6, IDNO = 7
            if response == 6:  # Пользователь нажал "Да"
                logger.info("Пользователь согласился на перезапуск с правами администратора")
                restart_as_admin()
                sys.exit(0)  # Выходим, так как приложение перезапускается с правами админа
            else:  # Пользователь нажал "Нет"
                logger.info("Пользователь отклонил запрос прав администратора")
                return False
        except Exception as e:
            logger.error(f"Ошибка при показе диалога: {e}")
            # Если не удалось показать диалог, пробуем перезапустить автоматически
            logger.info("Попытка автоматического перезапуска с правами администратора")
            if restart_as_admin():
                sys.exit(0)  # Выходим для перезапуска
            else:
                return False
        
        return False

