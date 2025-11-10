"""
Модуль блокировки сайтов и приложений
"""
import os
import psutil
import logging
from typing import List
from pathlib import Path

logger = logging.getLogger(__name__)


class Blocker:
    """
    Класс для блокировки сайтов и приложений
    
    Блокирует сайты через файл hosts и завершает процессы приложений.
    """
    
    def __init__(self):
        """Инициализация блокировщика"""
        self.hosts_path = Path(r"C:\Windows\System32\drivers\etc\hosts")
        self.blocked_sites = set()
        self.blocked_apps = set()
        self.is_blocking_enabled = False
    
    def enable_blocking(self):
        """Включение блокировки"""
        self.is_blocking_enabled = True
        logger.info("Блокировка включена")
    
    def disable_blocking(self):
        """Отключение блокировки"""
        self.is_blocking_enabled = False
        logger.info("Блокировка отключена")
    
    def block_site(self, url: str) -> bool:
        """
        Блокировка сайта через файл hosts
        
        Args:
            url: URL сайта для блокировки (например, "youtube.com")
            
        Returns:
            bool: True если успешно заблокирован
        """
        try:
            # Убираем протокол и путь, оставляем только домен
            domain = url.replace('http://', '').replace('https://', '').split('/')[0].strip()
            # Убираем www. если есть
            if domain.startswith('www.'):
                domain = domain[4:]
            
            if not domain:
                logger.error(f"Пустой домен после обработки URL: {url}")
                return False
            
            if not self.is_blocking_enabled:
                logger.warning(f"Блокировка отключена, сайт {domain} не будет заблокирован")
                # Не возвращаем False, чтобы можно было добавить в список даже при отключенной блокировке
                self.blocked_sites.add(domain)
                return False
            
            # Проверяем, не заблокирован ли уже
            if domain in self.blocked_sites:
                logger.info(f"Сайт {domain} уже в списке блокировки")
            
            # Читаем текущий hosts файл
            try:
                with open(self.hosts_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except PermissionError:
                logger.error("Нет прав для чтения hosts файл. Запустите от имени администратора.")
                return False
            except FileNotFoundError:
                logger.error(f"Файл hosts не найден: {self.hosts_path}")
                return False
            
            # Проверяем, нет ли уже такой записи (более точная проверка)
            lines = content.split('\n')
            domain_found = False
            for line in lines:
                line = line.strip()
                # Пропускаем комментарии и пустые строки
                if not line or line.startswith('#'):
                    continue
                # Проверяем, содержит ли строка наш домен
                if domain in line and ('127.0.0.1' in line or '::1' in line):
                    domain_found = True
                    break
            
            if domain_found:
                logger.info(f"Сайт {domain} уже присутствует в hosts")
                self.blocked_sites.add(domain)
                return True
            
            # Добавляем запись в hosts
            try:
                with open(self.hosts_path, 'a', encoding='utf-8') as f:
                    # Добавляем пустую строку перед новой записью для читаемости
                    if not content.endswith('\n'):
                        f.write('\n')
                    f.write(f"# SaveConfe block: {domain}\n")
                    f.write(f"127.0.0.1 {domain}\n")
                    f.write(f"::1 {domain}\n")
                
                self.blocked_sites.add(domain)
                logger.info(f"Сайт {domain} успешно заблокирован в hosts файле")
                return True
            except PermissionError:
                logger.error("Нет прав для записи в hosts файл. Запустите от имени администратора.")
                # Добавляем в список, даже если не удалось записать в hosts
                self.blocked_sites.add(domain)
                return False
            except Exception as e:
                logger.error(f"Ошибка записи в hosts файл: {e}")
                return False
        except Exception as e:
            logger.error(f"Ошибка блокировки сайта {url}: {e}", exc_info=True)
            return False
    
    def unblock_site(self, url: str) -> bool:
        """
        Разблокировка сайта
        
        Args:
            url: URL сайта для разблокировки
            
        Returns:
            bool: True если успешно разблокирован
        """
        try:
            domain = url.replace('http://', '').replace('https://', '').split('/')[0].strip()
            # Убираем www. если есть
            if domain.startswith('www.'):
                domain = domain[4:]
            
            if not domain:
                logger.error(f"Пустой домен после обработки URL: {url}")
                return False
            
            # Читаем hosts файл
            try:
                with open(self.hosts_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
            except PermissionError:
                logger.error("Нет прав для чтения hosts файла")
                return False
            except FileNotFoundError:
                logger.error(f"Файл hosts не найден: {self.hosts_path}")
                return False
            
            # Удаляем строки с этим доменом (более точное удаление)
            new_lines = []
            removed = False
            skip_next_comment = False
            
            for i, line in enumerate(lines):
                line_stripped = line.strip()
                
                # Пропускаем комментарий SaveConfe для этого домена
                if f"# SaveConfe block: {domain}" in line:
                    skip_next_comment = True
                    removed = True
                    continue
                
                # Пропускаем строки с доменом (127.0.0.1 или ::1)
                if domain in line_stripped and ('127.0.0.1' in line_stripped or '::1' in line_stripped):
                    removed = True
                    continue
                
                # Оставляем все остальные строки
                new_lines.append(line)
            
            if removed:
                # Записываем обратно
                try:
                    with open(self.hosts_path, 'w', encoding='utf-8') as f:
                        f.writelines(new_lines)
                    self.blocked_sites.discard(domain)
                    logger.info(f"Сайт {domain} разблокирован (удалён из hosts)")
                    return True
                except PermissionError:
                    logger.error("Нет прав для записи в hosts файл")
                    return False
            else:
                logger.info(f"Сайт {domain} не найден в hosts (возможно, уже разблокирован)")
                self.blocked_sites.discard(domain)
                return True
        except Exception as e:
            logger.error(f"Ошибка разблокировки сайта {url}: {e}", exc_info=True)
            return False
    
    def block_app(self, app_path: str) -> bool:
        """
        Добавление приложения в список блокировки
        
        Args:
            app_path: Путь к исполняемому файлу приложения
            
        Returns:
            bool: True если успешно добавлено
        """
        try:
            normalized_path = os.path.normpath(app_path).lower()
            self.blocked_apps.add(normalized_path)
            logger.info(f"Приложение добавлено в список блокировки: {app_path}")
            return True
        except Exception as e:
            logger.error(f"Ошибка блокировки приложения {app_path}: {e}")
            return False
    
    def unblock_app(self, app_path: str) -> bool:
        """
        Удаление приложения из списка блокировки
        
        Args:
            app_path: Путь к исполняемому файлу приложения
            
        Returns:
            bool: True если успешно удалено
        """
        try:
            normalized_path = os.path.normpath(app_path).lower()
            self.blocked_apps.discard(normalized_path)
            logger.info(f"Приложение удалено из списка блокировки: {app_path}")
            return True
        except Exception as e:
            logger.error(f"Ошибка разблокировки приложения {app_path}: {e}")
            return False
    
    def kill_blocked_apps(self) -> int:
        """
        Завершение всех заблокированных процессов
        
        Returns:
            int: Количество завершённых процессов
        """
        if not self.is_blocking_enabled:
            return 0
        
        killed_count = 0
        try:
            for proc in psutil.process_iter(['pid', 'name', 'exe']):
                try:
                    # Безопасное получение пути к исполняемому файлу
                    exe_path = proc.info.get('exe')
                    if exe_path and isinstance(exe_path, str):
                        exe_path = exe_path.lower()
                        normalized_exe = os.path.normpath(exe_path).lower()
                        # Проверяем, есть ли это приложение в списке блокировки
                        for blocked_path in self.blocked_apps:
                            if normalized_exe.endswith(blocked_path) or blocked_path in normalized_exe:
                                try:
                                    proc.terminate()
                                    killed_count += 1
                                    proc_name = proc.info.get('name', 'Unknown')
                                    proc_pid = proc.info.get('pid', 'Unknown')
                                    logger.info(f"Завершён процесс: {proc_name} (PID: {proc_pid})")
                                except (psutil.NoSuchProcess, psutil.AccessDenied):
                                    # Процесс уже завершён или нет прав
                                    pass
                                break
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
                except Exception as e:
                    # Игнорируем другие ошибки для отдельных процессов
                    logger.debug(f"Ошибка обработки процесса: {e}")
                    continue
        except Exception as e:
            logger.error(f"Ошибка при завершении процессов: {e}", exc_info=True)
        
        return killed_count
    
    def get_running_blocked_apps(self) -> List[dict]:
        """
        Получение списка запущенных заблокированных приложений
        
        Returns:
            List[dict]: Список словарей с информацией о процессах
        """
        running_apps = []
        try:
            for proc in psutil.process_iter(['pid', 'name', 'exe']):
                try:
                    # Безопасное получение пути к исполняемому файлу
                    exe_path = proc.info.get('exe')
                    if exe_path and isinstance(exe_path, str):
                        exe_path = exe_path.lower()
                        normalized_exe = os.path.normpath(exe_path).lower()
                        for blocked_path in self.blocked_apps:
                            if normalized_exe.endswith(blocked_path) or blocked_path in normalized_exe:
                                running_apps.append({
                                    'pid': proc.info.get('pid', 0),
                                    'name': proc.info.get('name', 'Unknown'),
                                    'path': exe_path
                                })
                                break
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
                except Exception as e:
                    # Игнорируем ошибки для отдельных процессов
                    logger.debug(f"Ошибка обработки процесса: {e}")
                    continue
        except Exception as e:
            logger.error(f"Ошибка при получении списка процессов: {e}", exc_info=True)
        
        return running_apps
    
    def load_blocked_sites(self, sites: List[str]):
        """
        Загрузка списка заблокированных сайтов
        
        Args:
            sites: Список URL сайтов (будут нормализованы)
        """
        normalized_sites = set()
        for site in sites:
            try:
                # Нормализуем домен так же, как в block_site
                domain = site.replace('http://', '').replace('https://', '').split('/')[0].strip()
                if domain.startswith('www.'):
                    domain = domain[4:]
                if domain:
                    normalized_sites.add(domain)
            except Exception as e:
                logger.warning(f"Ошибка нормализации сайта {site}: {e}")
        
        self.blocked_sites = normalized_sites
        logger.info(f"Загружено {len(normalized_sites)} заблокированных сайтов")
    
    def load_blocked_apps(self, apps: List[str]):
        """Загрузка списка заблокированных приложений"""
        self.blocked_apps = {os.path.normpath(app).lower() for app in apps}
        logger.info(f"Загружено {len(apps)} заблокированных приложений")

