"""
Модуль автозапуска приложения при старте Windows
"""
import os
import winreg
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class AutostartManager:
    """
    Менеджер автозапуска приложения
    
    Добавляет/удаляет приложение в автозагрузку Windows через реестр.
    """
    
    def __init__(self, app_name: str = "SaveConfe"):
        """
        Инициализация менеджера автозапуска
        
        Args:
            app_name: Название приложения в автозагрузке
        """
        self.app_name = app_name
        self.registry_key = r"Software\Microsoft\Windows\CurrentVersion\Run"
    
    def is_enabled(self) -> bool:
        """
        Проверка, включён ли автозапуск
        
        Returns:
            bool: True если автозапуск включён
        """
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.registry_key)
            try:
                value, _ = winreg.QueryValueEx(key, self.app_name)
                winreg.CloseKey(key)
                return bool(value)
            except FileNotFoundError:
                winreg.CloseKey(key)
                return False
        except Exception as e:
            logger.error(f"Ошибка проверки автозапуска: {e}")
            return False
    
    def enable(self, app_path: str) -> bool:
        """
        Включение автозапуска
        
        Args:
            app_path: Полный путь к исполняемому файлу приложения
            
        Returns:
            bool: True если успешно включено
        """
        try:
            # Нормализуем путь
            app_path = os.path.abspath(app_path)
            
            if not os.path.exists(app_path):
                logger.error(f"Файл не найден: {app_path}")
                return False
            
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                self.registry_key,
                0,
                winreg.KEY_SET_VALUE
            )
            
            winreg.SetValueEx(key, self.app_name, 0, winreg.REG_SZ, app_path)
            winreg.CloseKey(key)
            
            logger.info(f"Автозапуск включён для {app_path}")
            return True
        except Exception as e:
            logger.error(f"Ошибка включения автозапуска: {e}")
            return False
    
    def disable(self) -> bool:
        """
        Отключение автозапуска
        
        Returns:
            bool: True если успешно отключено
        """
        try:
            if not self.is_enabled():
                logger.info("Автозапуск уже отключён")
                return True
            
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                self.registry_key,
                0,
                winreg.KEY_SET_VALUE
            )
            
            winreg.DeleteValue(key, self.app_name)
            winreg.CloseKey(key)
            
            logger.info("Автозапуск отключён")
            return True
        except FileNotFoundError:
            logger.info("Автозапуск не был включён")
            return True
        except Exception as e:
            logger.error(f"Ошибка отключения автозапуска: {e}")
            return False

