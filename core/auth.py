"""
Модуль авторизации и управления паролями
"""
import bcrypt
import logging
from core.database import Database
from models.user import User, UserRole

logger = logging.getLogger(__name__)


class AuthManager:
    """
    Менеджер авторизации
    
    Управляет хешированием паролей, проверкой авторизации
    и созданием пользователей.
    """
    
    def __init__(self):
        """Инициализация менеджера авторизации"""
        self.db = Database()
        self.current_user = None
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Хеширование пароля с использованием bcrypt
        
        Args:
            password: Пароль в открытом виде
            
        Returns:
            str: Хешированный пароль
        """
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """
        Проверка пароля
        
        Args:
            password: Пароль в открытом виде
            password_hash: Хеш пароля из базы данных
            
        Returns:
            bool: True если пароль верный, False иначе
        """
        try:
            return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
        except Exception as e:
            logger.error(f"Ошибка проверки пароля: {e}")
            return False
    
    def create_admin(self, username: str, password: str) -> bool:
        """
        Создание администратора
        
        Args:
            username: Имя пользователя
            password: Пароль
            
        Returns:
            bool: True если успешно создан, False если уже существует
        """
        try:
            existing_user = self.db.get_user_by_username(username)
            if existing_user:
                logger.warning(f"Пользователь {username} уже существует")
                return False
            
            password_hash = self.hash_password(password)
            self.db.create_user(username, password_hash, UserRole.ADMIN)
            logger.info(f"Создан администратор: {username}")
            return True
        except Exception as e:
            logger.error(f"Ошибка создания администратора: {e}")
            return False
    
    def login(self, username: str, password: str) -> bool:
        """
        Авторизация пользователя
        
        Args:
            username: Имя пользователя
            password: Пароль
            
        Returns:
            bool: True если авторизация успешна, False иначе
        """
        try:
            user = self.db.get_user_by_username(username)
            if not user:
                logger.warning(f"Пользователь {username} не найден")
                return False
            
            if self.verify_password(password, user.password_hash):
                self.current_user = user
                logger.info(f"Успешная авторизация: {username}")
                return True
            else:
                logger.warning(f"Неверный пароль для пользователя: {username}")
                return False
        except Exception as e:
            logger.error(f"Ошибка авторизации: {e}")
            return False
    
    def change_password(self, username: str, old_password: str, new_password: str) -> bool:
        """
        Смена пароля
        
        Args:
            username: Имя пользователя
            old_password: Старый пароль
            new_password: Новый пароль
            
        Returns:
            bool: True если пароль успешно изменён
        """
        try:
            if not self.login(username, old_password):
                return False
            
            session = self.db.get_session()
            try:
                user = session.query(User).filter(User.username == username).first()
                if user:
                    user.password_hash = self.hash_password(new_password)
                    session.commit()
                    logger.info(f"Пароль изменён для пользователя: {username}")
                    return True
                return False
            finally:
                session.close()
        except Exception as e:
            logger.error(f"Ошибка смены пароля: {e}")
            return False
    
    def is_authenticated(self) -> bool:
        """Проверка, авторизован ли текущий пользователь"""
        return self.current_user is not None
    
    def is_admin(self) -> bool:
        """Проверка, является ли текущий пользователь администратором"""
        return (self.current_user is not None and 
                self.current_user.role == UserRole.ADMIN)
    
    def logout(self):
        """Выход из системы"""
        self.current_user = None
        logger.info("Пользователь вышел из системы")

