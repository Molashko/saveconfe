"""
Модуль для работы с базой данных MySQL
"""
import os
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv
import logging

from models.user import User, UserRole
from models.site_rule import SiteRule
from models.app_rule import AppRule
from models.usage_log import UsageLog, ItemType
from models.base import Base

# Загружаем переменные окружения (будет перезагружено в __init__)
# Сначала пробуем database.env, потом .env
env_file = 'database.env' if os.path.exists('database.env') else '.env'
load_dotenv(env_file)

logger = logging.getLogger(__name__)


class Database:
    """
    Класс для работы с базой данных MySQL
    
    Предоставляет методы для CRUD-операций с пользователями,
    правилами блокировки и логами использования.
    """
    
    def __init__(self):
        """Инициализация подключения к базе данных"""
        # Загружаем из database.env или .env
        env_file = 'database.env' if os.path.exists('database.env') else '.env'
        load_dotenv(env_file)
        
        self.host = os.getenv('DB_HOST', 'localhost')
        self.port = int(os.getenv('DB_PORT', 3306))
        self.user = os.getenv('DB_USER', 'root')
        self.password = os.getenv('DB_PASSWORD', '')
        self.database = os.getenv('DB_NAME', 'saveconfe')
        
        self.engine = None
        self.SessionLocal = None
        self._ensure_database_exists()
        self._connect()
    
    def _ensure_database_exists(self):
        """Проверка и создание базы данных, если её нет"""
        try:
            import pymysql
            # Подключаемся к MySQL без указания базы данных
            connection = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                charset='utf8mb4'
            )
            
            with connection.cursor() as cursor:
                # Проверяем, существует ли база данных
                cursor.execute("SHOW DATABASES LIKE %s", (self.database,))
                exists = cursor.fetchone()
                
                if not exists:
                    logger.info(f"База данных {self.database} не найдена, создание...")
                    cursor.execute(
                        f"CREATE DATABASE {self.database} "
                        f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
                    )
                    connection.commit()
                    logger.info(f"База данных {self.database} создана успешно")
                else:
                    logger.info(f"База данных {self.database} уже существует")
            
            connection.close()
        except ImportError:
            logger.warning("pymysql не установлен, автоматическое создание БД недоступно")
        except Exception as e:
            logger.warning(f"Не удалось проверить/создать базу данных: {e}")
            # Продолжаем выполнение, возможно база уже существует
    
    def _connect(self):
        """Создание подключения к базе данных"""
        try:
            connection_string = (
                f"mysql+pymysql://{self.user}:{self.password}@"
                f"{self.host}:{self.port}/{self.database}?charset=utf8mb4"
            )
            self.engine = create_engine(
                connection_string,
                pool_pre_ping=True,
                echo=False
            )
            self.SessionLocal = sessionmaker(bind=self.engine)
            logger.info(f"Подключение к базе данных {self.database} установлено")
        except Exception as e:
            logger.error(f"Ошибка подключения к базе данных: {e}")
            raise
    
    def get_session(self) -> Session:
        """Получение сессии базы данных"""
        return self.SessionLocal()
    
    # Методы для работы с пользователями
    def create_user(self, username: str, password_hash: str, role: UserRole = UserRole.ADMIN) -> User:
        """Создание нового пользователя"""
        session = self.get_session()
        try:
            user = User(username=username, password_hash=password_hash, role=role)
            session.add(user)
            session.commit()
            session.refresh(user)
            logger.info(f"Создан пользователь: {username}")
            return user
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Ошибка создания пользователя: {e}")
            raise
        finally:
            session.close()
    
    def get_user_by_username(self, username: str) -> User:
        """Получение пользователя по имени"""
        session = self.get_session()
        try:
            return session.query(User).filter(User.username == username).first()
        finally:
            session.close()
    
    # Методы для работы с правилами сайтов
    def add_site_rule(self, url: str, time_limit: int = 0, schedule_start=None, schedule_end=None) -> SiteRule:
        """Добавление правила блокировки сайта"""
        session = self.get_session()
        try:
            rule = SiteRule(url=url, time_limit=time_limit, 
                          schedule_start=schedule_start, schedule_end=schedule_end)
            session.add(rule)
            session.commit()
            session.refresh(rule)
            logger.info(f"Добавлено правило для сайта: {url}")
            return rule
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Ошибка добавления правила сайта: {e}")
            raise
        finally:
            session.close()
    
    def get_all_site_rules(self) -> list:
        """Получение всех правил блокировки сайтов"""
        session = self.get_session()
        try:
            return session.query(SiteRule).all()
        finally:
            session.close()
    
    def delete_site_rule(self, rule_id: int) -> bool:
        """Удаление правила блокировки сайта"""
        session = self.get_session()
        try:
            rule = session.query(SiteRule).filter(SiteRule.id == rule_id).first()
            if rule:
                session.delete(rule)
                session.commit()
                logger.info(f"Удалено правило сайта с ID: {rule_id}")
                return True
            return False
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Ошибка удаления правила сайта: {e}")
            raise
        finally:
            session.close()
    
    # Методы для работы с правилами приложений
    def add_app_rule(self, app_path: str, app_name: str, time_limit: int = 0,
                     schedule_start=None, schedule_end=None) -> AppRule:
        """Добавление правила блокировки приложения"""
        session = self.get_session()
        try:
            rule = AppRule(app_path=app_path, app_name=app_name, time_limit=time_limit,
                          schedule_start=schedule_start, schedule_end=schedule_end)
            session.add(rule)
            session.commit()
            session.refresh(rule)
            logger.info(f"Добавлено правило для приложения: {app_name}")
            return rule
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Ошибка добавления правила приложения: {e}")
            raise
        finally:
            session.close()
    
    def get_all_app_rules(self) -> list:
        """Получение всех правил блокировки приложений"""
        session = self.get_session()
        try:
            return session.query(AppRule).all()
        finally:
            session.close()
    
    def delete_app_rule(self, rule_id: int) -> bool:
        """Удаление правила блокировки приложения"""
        session = self.get_session()
        try:
            rule = session.query(AppRule).filter(AppRule.id == rule_id).first()
            if rule:
                session.delete(rule)
                session.commit()
                logger.info(f"Удалено правило приложения с ID: {rule_id}")
                return True
            return False
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Ошибка удаления правила приложения: {e}")
            raise
        finally:
            session.close()
    
    # Методы для работы с логами
    def add_usage_log(self, item_type: ItemType, item_name: str, 
                     start_time=None, end_time=None, duration: float = 0.0) -> UsageLog:
        """Добавление лога использования"""
        session = self.get_session()
        try:
            from datetime import datetime
            if start_time is None:
                start_time = datetime.now()
            
            log = UsageLog(item_type=item_type, item_name=item_name,
                          start_time=start_time, end_time=end_time, duration=duration)
            session.add(log)
            session.commit()
            session.refresh(log)
            return log
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Ошибка добавления лога: {e}")
            raise
        finally:
            session.close()
    
    def get_usage_logs(self, limit: int = 100) -> list:
        """Получение логов использования"""
        session = self.get_session()
        try:
            return session.query(UsageLog).order_by(UsageLog.start_time.desc()).limit(limit).all()
        finally:
            session.close()


def init_db():
    """
    Инициализация базы данных - создание всех таблиц
    
    Returns:
        bool: True если успешно, False в случае ошибки
    """
    try:
        # Создаём все таблицы
        Base.metadata.create_all(Database().engine)
        logger.info("База данных инициализирована успешно")
        return True
    except Exception as e:
        logger.error(f"Ошибка инициализации базы данных: {e}")
        return False

