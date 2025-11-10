"""
Модель правила блокировки сайта
"""
from sqlalchemy import Column, Integer, String, Time, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base


class SiteRule(Base):
    """
    Модель правила блокировки сайта
    
    Attributes:
        id: Уникальный идентификатор
        url: URL сайта для блокировки
        time_limit: Лимит времени в минутах (0 = без лимита)
        schedule_start: Время начала разрешённого доступа
        schedule_end: Время окончания разрешённого доступа
    """
    __tablename__ = 'blocked_sites'

    id = Column(Integer, primary_key=True, autoincrement=True)
    url = Column(String(255), nullable=False, unique=True)
    time_limit = Column(Integer, default=0)  # в минутах, 0 = без лимита
    schedule_start = Column(Time, nullable=True)  # например, 09:00
    schedule_end = Column(Time, nullable=True)  # например, 20:00

    def __repr__(self):
        return f"<SiteRule(id={self.id}, url='{self.url}', time_limit={self.time_limit})>"

