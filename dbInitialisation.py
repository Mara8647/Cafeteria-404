import sqlite3

def init_db():
    #создание связи с БД (создается файл cafe в котором будут храниться данные)"
    connection = sqlite3.connect('cafe.db')
    #создаем указатель для отправки SQL запросы в БД и получения результатов"
    сursor = connection.cursor()
    #Таблица для юзеров
    сursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                payment_type TEXT CHECK(payment_type IN ('single','subscription')),
                user_balance REAL NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('student', 'cook', 'admin')),
                allergies TEXT NOT NULL CHECK(allergies IN ('none', 'milk', 'eggs', 'peanuts', 'seafood', 'wheat', 'soy'))
            )
        ''')
    #Таблица для меню на каждый день
    сursor.execute('''
            CREATE TABLE IF NOT EXISTS menu (
                id INTEGER PRIMARY KEY,
                meal_type TEXT NOT NULL CHECK(meal_type IN ('breakfast', 'lunch')),
                name TEXT NOT NULL,
                price REAL NOT NULL,
                allergies TEXT NOT NULL CHECK(allergies IN ('none', 'milk', 'eggs', 'peanuts', 'seafood', 'wheat', 'soy')),
                date TEXT NOT NULL DEFAULT CURRENT_DATE
            )
        ''')
    #Таблица для оплат
    сursor.execute('''
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                payment_type TEXT NOT NULL CHECK(payment_type IN ('single','subscription')),
                date TEXT NOT NULL DEFAULT CURRENT_DATE,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        ''')
    #Таблица для подсчета кому что выдано и в каком
    сursor.execute('''
            CREATE TABLE IF NOT EXISTS meals (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                menu_id INTEGER NOT NULL,
                date TEXT NOT NULL DEFAULT CURRENT_DATE,
                FOREIGN KEY(user_id) REFERENCES users(id),
                FOREIGN KEY(menu_id) REFERENCES menu(id),
                UNIQUE(user_id, menu_id, date)
            )
        ''')
    #Таблица для запросов на покупку
    сursor.execute('''
            CREATE TABLE IF NOT EXISTS purchase_requests (
                id INTEGER PRIMARY KEY,
                cook_id INTEGER NOT NULL,
                product_name TEXT NOT NULL,
                quantity REAL NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending', 'approved', 'rejected')),
                created_at TEXT NOT NULL DEFAULT CURRENT_DATE,
                FOREIGN KEY(cook_id) REFERENCES users(id)
            )
        ''')



# Запуск инициализации при прямом вызове скрипта
if __name__ == '__main__':
    init_db()