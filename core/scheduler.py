"""
Модуль планировщика времени использования
"""
from datetime import datetime, time, timedelta
from typing import Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class Scheduler:
    """
    Планировщик времени использования
    
    Управляет расписанием доступа и лимитами времени.
    """
    
    def __init__(self):
        """Инициализация планировщика"""
        self.time_limits: Dict[str, int] = {}  # Лимиты времени в минутах
        self.used_time: Dict[str, float] = {}  # Использованное время в минутах
        self.schedules: Dict[str, tuple] = {}  # Расписания (start_time, end_time)
        self.is_enabled = True
    
    def set_time_limit(self, item_name: str, minutes: int):
        """
        Установка лимита времени для элемента
        
        Args:
            item_name: Название сайта или приложения
            minutes: Лимит времени в минутах (0 = без лимита)
        """
        self.time_limits[item_name] = minutes
        if item_name not in self.used_time:
            self.used_time[item_name] = 0.0
        logger.info(f"Установлен лимит {minutes} минут для {item_name}")
    
    def get_time_limit(self, item_name: str) -> int:
        """
        Получение лимита времени для элемента
        
        Args:
            item_name: Название сайта или приложения
            
        Returns:
            int: Лимит времени в минутах (0 = без лимита)
        """
        return self.time_limits.get(item_name, 0)
    
    def add_used_time(self, item_name: str, minutes: float):
        """
        Добавление использованного времени
        
        Args:
            item_name: Название сайта или приложения
            minutes: Использованное время в минутах
        """
        if item_name not in self.used_time:
            self.used_time[item_name] = 0.0
        self.used_time[item_name] += minutes
        logger.debug(f"Добавлено {minutes} минут использования для {item_name}")
    
    def get_used_time(self, item_name: str) -> float:
        """
        Получение использованного времени
        
        Args:
            item_name: Название сайта или приложения
            
        Returns:
            float: Использованное время в минутах
        """
        return self.used_time.get(item_name, 0.0)
    
    def get_remaining_time(self, item_name: str) -> Optional[float]:
        """
        Получение оставшегося времени
        
        Args:
            item_name: Название сайта или приложения
            
        Returns:
            Optional[float]: Оставшееся время в минутах или None если лимита нет
        """
        limit = self.get_time_limit(item_name)
        if limit == 0:
            return None  # Без лимита
        
        used = self.get_used_time(item_name)
        remaining = limit - used
        return max(0.0, remaining)
    
    def is_time_limit_exceeded(self, item_name: str) -> bool:
        """
        Проверка, превышен ли лимит времени
        
        Args:
            item_name: Название сайта или приложения
            
        Returns:
            bool: True если лимит превышен
        """
        limit = self.get_time_limit(item_name)
        if limit == 0:
            return False  # Без лимита
        
        used = self.get_used_time(item_name)
        return used >= limit
    
    def set_schedule(self, item_name: str, start_time: time, end_time: time):
        """
        Установка расписания доступа
        
        Args:
            item_name: Название сайта или приложения
            start_time: Время начала разрешённого доступа
            end_time: Время окончания разрешённого доступа
        """
        self.schedules[item_name] = (start_time, end_time)
        logger.info(f"Установлено расписание для {item_name}: {start_time} - {end_time}")
    
    def is_within_schedule(self, item_name: str, current_time: Optional[datetime] = None) -> bool:
        """
        Проверка, находится ли текущее время в разрешённом расписании
        
        Args:
            item_name: Название сайта или приложения
            current_time: Текущее время (если None, используется datetime.now())
            
        Returns:
            bool: True если время в разрешённом диапазоне
        """
        if item_name not in self.schedules:
            return True  # Нет расписания - всегда разрешено
        
        if current_time is None:
            current_time = datetime.now()
        
        schedule = self.schedules[item_name]
        start_time, end_time = schedule
        
        current_time_only = current_time.time()
        
        # Если время начала больше времени окончания, значит расписание переходит через полночь
        if start_time > end_time:
            return current_time_only >= start_time or current_time_only <= end_time
        else:
            return start_time <= current_time_only <= end_time
    
    def reset_daily_usage(self):
        """Сброс ежедневного использования (вызывать в начале дня)"""
        self.used_time.clear()
        logger.info("Ежедневное использование сброшено")
    
    def is_access_allowed(self, item_name: str) -> Tuple[bool, str]:
        """
        Проверка, разрешён ли доступ к элементу
        
        Args:
            item_name: Название сайта или приложения
            
        Returns:
            tuple[bool, str]: (разрешён ли доступ, причина отказа если нет)
        """
        if not self.is_enabled:
            return True, ""
        
        # Проверка расписания
        if not self.is_within_schedule(item_name):
            schedule = self.schedules.get(item_name)
            if schedule:
                return False, f"Вне разрешённого времени ({schedule[0]} - {schedule[1]})"
        
        # Проверка лимита времени
        if self.is_time_limit_exceeded(item_name):
            limit = self.get_time_limit(item_name)
            return False, f"Превышен лимит времени ({limit} минут)"
        
        return True, ""

