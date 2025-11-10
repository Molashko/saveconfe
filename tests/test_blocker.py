"""
Тесты для модуля блокировки
"""
import pytest
from core.blocker import Blocker


def test_blocker_initialization():
    """Тест инициализации блокировщика"""
    blocker = Blocker()
    assert not blocker.is_blocking_enabled
    assert len(blocker.blocked_sites) == 0
    assert len(blocker.blocked_apps) == 0


def test_enable_disable_blocking():
    """Тест включения/отключения блокировки"""
    blocker = Blocker()
    
    blocker.enable_blocking()
    assert blocker.is_blocking_enabled
    
    blocker.disable_blocking()
    assert not blocker.is_blocking_enabled


def test_load_blocked_sites():
    """Тест загрузки списка заблокированных сайтов"""
    blocker = Blocker()
    sites = ["youtube.com", "facebook.com", "twitter.com"]
    
    blocker.load_blocked_sites(sites)
    assert len(blocker.blocked_sites) == 3
    assert "youtube.com" in blocker.blocked_sites


def test_load_blocked_apps():
    """Тест загрузки списка заблокированных приложений"""
    blocker = Blocker()
    apps = ["C:\\Program Files\\App\\app.exe", "C:\\Games\\game.exe"]
    
    blocker.load_blocked_apps(apps)
    assert len(blocker.blocked_apps) == 2


def test_block_unblock_app():
    """Тест блокировки/разблокировки приложения"""
    blocker = Blocker()
    app_path = "C:\\Test\\app.exe"
    
    result = blocker.block_app(app_path)
    assert result
    assert app_path.lower() in blocker.blocked_apps
    
    result = blocker.unblock_app(app_path)
    assert result
    assert app_path.lower() not in blocker.blocked_apps

