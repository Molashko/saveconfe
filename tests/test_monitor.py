"""
Тесты для модуля мониторинга
"""
import pytest
from core.monitor import Monitor
from core.blocker import Blocker
from core.scheduler import Scheduler
from core.database import Database


def test_monitor_initialization():
    """Тест инициализации монитора"""
    blocker = Blocker()
    scheduler = Scheduler()
    db = Database()
    
    monitor = Monitor(blocker, scheduler, db)
    
    assert not monitor.is_monitoring
    assert monitor.check_interval == 5
    assert len(monitor.active_processes) == 0


def test_start_stop_monitoring():
    """Тест запуска/остановки мониторинга"""
    blocker = Blocker()
    scheduler = Scheduler()
    db = Database()
    
    monitor = Monitor(blocker, scheduler, db)
    
    monitor.start_monitoring()
    assert monitor.is_monitoring
    
    monitor.stop_monitoring()
    assert not monitor.is_monitoring

