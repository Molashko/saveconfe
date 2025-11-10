"""
Модель пользователя
"""
from sqlalchemy import Column, Integer, String, Enum
import enum
from .base import Base


class UserRole(enum.Enum):
    """Роли пользователей"""
    ADMIN = "admin"
    CHILD = "child"


class User(Base):
    """
    Модель пользователя системы
    
    Attributes:
        id: Уникальный идентификатор
        username: Имя пользователя
        password_hash: Хеш пароля
        role: Роль пользователя (admin/child)
    """
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.ADMIN, nullable=False)

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', role='{self.role.value}')>"

