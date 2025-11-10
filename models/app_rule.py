"""
Модель правила блокировки приложения
"""
from sqlalchemy import Column, Integer, String, Time
from .base import Base


class AppRule(Base):
    """
    Модель правила блокировки приложения
    
    Attributes:
        id: Уникальный идентификатор
        app_path: Путь к исполняемому файлу приложения
        app_name: Название приложения
        time_limit: Лимит времени в минутах (0 = без лимита)
        schedule_start: Время начала разрешённого доступа
        schedule_end: Время окончания разрешённого доступа
    """
    __tablename__ = 'blocked_apps'

    id = Column(Integer, primary_key=True, autoincrement=True)
    app_path = Column(String(500), nullable=False, unique=True)
    app_name = Column(String(255), nullable=False)
    time_limit = Column(Integer, default=0)  # в минутах, 0 = без лимита
    schedule_start = Column(Time, nullable=True)
    schedule_end = Column(Time, nullable=True)

    def __repr__(self):
        return f"<AppRule(id={self.id}, app_name='{self.app_name}', app_path='{self.app_path}')>"

