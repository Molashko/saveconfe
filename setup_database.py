"""
Скрипт для автоматического создания базы данных MySQL
"""
import os
import sys
from dotenv import load_dotenv

# Настройка кодировки для Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

def create_database():
    """Создание базы данных saveconfe в MySQL"""
    try:
        # Загружаем переменные окружения из database.env или .env
        env_file = 'database.env' if os.path.exists('database.env') else '.env'
        load_dotenv(env_file)
        
        print("=" * 60)
        print("Создание базы данных MySQL для SaveConfe")
        print("=" * 60)
        print()
        
        # Получаем настройки
        host = os.getenv('DB_HOST', 'localhost')
        port = int(os.getenv('DB_PORT', 3306))
        user = os.getenv('DB_USER', 'root')
        password = os.getenv('DB_PASSWORD', '')
        database_name = os.getenv('DB_NAME', 'saveconfe')
        
        print(f"Настройки подключения:")
        print(f"  Host: {host}")
        print(f"  Port: {port}")
        print(f"  User: {user}")
        print(f"  Database: {database_name}")
        print()
        
        # Импортируем pymysql
        try:
            import pymysql
        except ImportError:
            print("❌ Ошибка: pymysql не установлен")
            print("Установите: pip install pymysql")
            return False
        
        # Подключаемся к MySQL (без указания базы данных)
        print("Подключение к MySQL серверу...")
        try:
            connection = pymysql.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                charset='utf8mb4'
            )
            print("[OK] Подключение к MySQL успешно!")
            print()
        except pymysql.Error as e:
            print(f"[ERROR] Ошибка подключения к MySQL: {e}")
            print()
            print("Возможные решения:")
            print("  1. Убедитесь, что MySQL запущен")
            print("  2. Проверьте настройки в database.env")
            print("  3. Проверьте правильность пароля")
            return False
        
        # Создаём базу данных
        try:
            with connection.cursor() as cursor:
                # Проверяем, существует ли база данных
                cursor.execute("SHOW DATABASES LIKE %s", (database_name,))
                exists = cursor.fetchone()
                
                if exists:
                    print(f"[INFO] База данных '{database_name}' уже существует")
                    print("Пропускаем создание (база уже есть)")
                    connection.close()
                    return True
                
                # Создаём базу данных
                print(f"Создание базы данных '{database_name}'...")
                cursor.execute(
                    f"CREATE DATABASE {database_name} "
                    f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
                )
                connection.commit()
                print(f"[OK] База данных '{database_name}' создана успешно!")
                print()
                
                # Показываем список баз данных
                cursor.execute("SHOW DATABASES")
                databases = cursor.fetchall()
                print("Доступные базы данных:")
                for db in databases:
                    db_name = db[0]
                    marker = " [создана]" if db_name == database_name else ""
                    print(f"  - {db_name}{marker}")
            
            connection.close()
            print()
            print("=" * 60)
            print("[OK] База данных создана успешно!")
            print("=" * 60)
            return True
            
        except pymysql.Error as e:
            print(f"[ERROR] Ошибка при создании базы данных: {e}")
            connection.close()
            return False
            
    except Exception as e:
        print(f"[ERROR] Неожиданная ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

def init_tables():
    """Инициализация таблиц в базе данных"""
    try:
        print()
        print("=" * 60)
        print("Инициализация таблиц")
        print("=" * 60)
        print()
        
        from core.database import init_db
        
        if init_db():
            print("[OK] Таблицы созданы успешно!")
            return True
        else:
            print("[ERROR] Ошибка создания таблиц")
            return False
    except Exception as e:
        print(f"[ERROR] Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        # Создаём базу данных
        if create_database():
            # Инициализируем таблицы
            init_tables()
            print()
            print("=" * 60)
            print("[OK] Настройка завершена!")
            print("=" * 60)
            print()
            print("Следующий шаг: запустите приложение")
            print("  python main.py")
        else:
            print()
            print("=" * 60)
            print("[ERROR] Не удалось создать базу данных")
            print("=" * 60)
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nПрервано пользователем")
        sys.exit(1)

