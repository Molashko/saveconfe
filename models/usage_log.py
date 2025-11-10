"""
Модель лога использования
"""
from sqlalchemy import Column, Integer, String, DateTime, Float, Enum
from datetime import datetime
import enum
from .base import Base


class ItemType(enum.Enum):
    """Типы элементов для логирования"""
    SITE = "site"
    APP = "app"


class UsageLog(Base):
    """
    Модель лога использования сайтов и приложений
    
    Attributes:
        id: Уникальный идентификатор
        item_type: Тип элемента (site/app)
        item_name: Название сайта или приложения
        start_time: Время начала использования
        end_time: Время окончания использования
        duration: Длительность в минутах
    """
    __tablename__ = 'usage_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    item_type = Column(Enum(ItemType), nullable=False)
    item_name = Column(String(255), nullable=False)
    start_time = Column(DateTime, default=datetime.now, nullable=False)
    end_time = Column(DateTime, nullable=True)
    duration = Column(Float, default=0.0)  # в минутах

    def __repr__(self):
        return f"<UsageLog(id={self.id}, item_type='{self.item_type.value}', item_name='{self.item_name}', duration={self.duration})>"

