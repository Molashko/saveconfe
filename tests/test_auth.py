"""
Тесты для модуля авторизации
"""
import pytest
from core.auth import AuthManager
from core.database import Database
from models.user import UserRole


def test_hash_password():
    """Тест хеширования пароля"""
    password = "test_password"
    hashed = AuthManager.hash_password(password)
    
    assert hashed != password
    assert len(hashed) > 0
    assert AuthManager.verify_password(password, hashed)


def test_verify_password():
    """Тест проверки пароля"""
    password = "test_password"
    hashed = AuthManager.hash_password(password)
    
    assert AuthManager.verify_password(password, hashed)
    assert not AuthManager.verify_password("wrong_password", hashed)


def test_create_admin():
    """Тест создания администратора"""
    auth = AuthManager()
    result = auth.create_admin("test_admin", "test_password")
    
    # Проверяем, что пользователь создан
    user = auth.db.get_user_by_username("test_admin")
    assert user is not None
    assert user.role == UserRole.ADMIN


def test_login():
    """Тест входа в систему"""
    auth = AuthManager()
    
    # Создаём пользователя
    auth.create_admin("test_user", "test_password")
    
    # Проверяем вход
    assert auth.login("test_user", "test_password")
    assert auth.is_authenticated()
    assert auth.is_admin()
    
    # Проверяем неверный пароль
    auth.logout()
    assert not auth.login("test_user", "wrong_password")
    assert not auth.is_authenticated()

