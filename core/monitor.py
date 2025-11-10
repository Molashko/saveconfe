"""
Модуль мониторинга процессов и активности
"""
import psutil
import time
import logging
from datetime import datetime
from typing import Dict, Optional
from threading import Thread, Event

from core.database import Database
from models.usage_log import ItemType

logger = logging.getLogger(__name__)


class Monitor:
    """
    Монитор процессов и активности
    
    Отслеживает запущенные процессы, записывает логи активности
    и проверяет правила блокировки.
    """
    
    def __init__(self, blocker, scheduler, database: Database):
        """
        Инициализация монитора
        
        Args:
            blocker: Экземпляр Blocker для блокировки
            scheduler: Экземпляр Scheduler для проверки лимитов
            database: Экземпляр Database для записи логов
        """
        self.blocker = blocker
        self.scheduler = scheduler
        self.db = database
        self.is_monitoring = False
        self.monitor_thread: Optional[Thread] = None
        self.stop_event = Event()
        self.active_processes: Dict[str, dict] = {}  # {app_path: {pid, start_time, log_id}}
        self.check_interval = 5  # Интервал проверки в секундах
    
    def start_monitoring(self):
        """Запуск мониторинга"""
        if self.is_monitoring:
            logger.warning("Мониторинг уже запущен")
            return
        
        self.is_monitoring = True
        self.stop_event.clear()
        self.monitor_thread = Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("Мониторинг запущен")
    
    def stop_monitoring(self):
        """Остановка мониторинга"""
        if not self.is_monitoring:
            return
        
        self.is_monitoring = False
        self.stop_event.set()
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        
        # Завершаем все активные логи
        self._finalize_all_logs()
        logger.info("Мониторинг остановлен")
    
    def _monitor_loop(self):
        """Основной цикл мониторинга"""
        while not self.stop_event.is_set():
            try:
                self._check_processes()
                self._check_blocked_apps()
                time.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Ошибка в цикле мониторинга: {e}")
                time.sleep(self.check_interval)
    
    def _check_processes(self):
        """Проверка запущенных процессов"""
        try:
            current_processes = {}
            
            # Получаем все процессы
            for proc in psutil.process_iter(['pid', 'name', 'exe', 'create_time']):
                try:
                    exe_path = proc.info.get('exe', '')
                    if not exe_path:
                        continue
                    
                    normalized_path = exe_path.lower()
                    
                    # Проверяем, есть ли это приложение в списке отслеживания
                    # (заблокированные приложения)
                    for blocked_path in self.blocker.blocked_apps:
                        if normalized_path.endswith(blocked_path) or blocked_path in normalized_path:
                            app_name = proc.info['name']
                            current_processes[normalized_path] = {
                                'pid': proc.info['pid'],
                                'name': app_name,
                                'path': exe_path,
                                'start_time': datetime.fromtimestamp(proc.info['create_time'])
                            }
                            break
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            
            # Обрабатываем новые процессы
            for app_path, proc_info in current_processes.items():
                if app_path not in self.active_processes:
                    # Новый процесс - начинаем логирование
                    self._start_logging(app_path, proc_info)
            
            # Обрабатываем завершённые процессы
            for app_path in list(self.active_processes.keys()):
                if app_path not in current_processes:
                    # Процесс завершён - завершаем логирование
                    self._stop_logging(app_path)
            
            # Обновляем информацию о времени использования
            self._update_usage_time()
            
        except Exception as e:
            logger.error(f"Ошибка при проверке процессов: {e}")
    
    def _start_logging(self, app_path: str, proc_info: dict):
        """Начало логирования использования приложения"""
        try:
            app_name = proc_info['name']
            start_time = proc_info['start_time']
            
            # Проверяем, разрешён ли доступ
            allowed, reason = self.scheduler.is_access_allowed(app_name)
            if not allowed:
                logger.info(f"Доступ к {app_name} запрещён: {reason}")
                # Завершаем процесс
                try:
                    proc = psutil.Process(proc_info['pid'])
                    proc.terminate()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
                return
            
            # Создаём лог
            log = self.db.add_usage_log(
                item_type=ItemType.APP,
                item_name=app_name,
                start_time=start_time
            )
            
            self.active_processes[app_path] = {
                'pid': proc_info['pid'],
                'start_time': start_time,
                'log_id': log.id,
                'name': app_name
            }
            
            logger.info(f"Начато логирование использования: {app_name}")
        except Exception as e:
            logger.error(f"Ошибка начала логирования: {e}")
    
    def _stop_logging(self, app_path: str):
        """Завершение логирования использования приложения"""
        try:
            if app_path not in self.active_processes:
                return
            
            proc_info = self.active_processes[app_path]
            app_name = proc_info['name']
            start_time = proc_info['start_time']
            log_id = proc_info['log_id']
            
            # Вычисляем длительность
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds() / 60  # в минутах
            
            # Обновляем лог в базе данных
            session = self.db.get_session()
            try:
                from models.usage_log import UsageLog
                log = session.query(UsageLog).filter(UsageLog.id == log_id).first()
                if log:
                    log.end_time = end_time
                    log.duration = duration
                    session.commit()
                    
                    # Обновляем использованное время в планировщике
                    self.scheduler.add_used_time(app_name, duration)
            finally:
                session.close()
            
            del self.active_processes[app_path]
            logger.info(f"Завершено логирование использования: {app_name} (длительность: {duration:.2f} мин)")
        except Exception as e:
            logger.error(f"Ошибка завершения логирования: {e}")
    
    def _update_usage_time(self):
        """Обновление времени использования для активных процессов"""
        current_time = datetime.now()
        for app_path, proc_info in self.active_processes.items():
            try:
                start_time = proc_info['start_time']
                duration = (current_time - start_time).total_seconds() / 60
                app_name = proc_info['name']
                
                # Проверяем лимит времени
                if self.scheduler.is_time_limit_exceeded(app_name):
                    logger.info(f"Превышен лимит времени для {app_name}, завершаем процесс")
                    try:
                        proc = psutil.Process(proc_info['pid'])
                        proc.terminate()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
            except Exception as e:
                logger.error(f"Ошибка обновления времени использования: {e}")
    
    def _check_blocked_apps(self):
        """Проверка и завершение заблокированных приложений"""
        if self.blocker.is_blocking_enabled:
            killed = self.blocker.kill_blocked_apps()
            if killed > 0:
                logger.info(f"Завершено {killed} заблокированных процессов")
    
    def _finalize_all_logs(self):
        """Завершение всех активных логов при остановке мониторинга"""
        for app_path in list(self.active_processes.keys()):
            self._stop_logging(app_path)

