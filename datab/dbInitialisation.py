import sqlite3
import os

def init_db():
    # Подключаемся к базе (если файла нет, он создастся)
    conn = sqlite3.connect('cafe.db')
    c = conn.cursor()

    # Таблица с пользователями
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            payment_type TEXT CHECK (payment_type IN ('single','subscription')),
            user_balance REAL NOT NULL,
            role TEXT NOT NULL CHECK (role IN ('student', 'cook', 'admin')),
            allergies TEXT NOT NULL
        )
    ''')

    # Таблица меню (завтраки, обеды)
    c.execute('''
        CREATE TABLE IF NOT EXISTS menu (
            id INTEGER PRIMARY KEY,
            meal_type TEXT NOT NULL CHECK(meal_type IN('breakfast', 'lunch')),
            name TEXT NOT NULL,
            price REAL NOT NULL,
            allergies TEXT NOT NULL,
            date TEXT NOT NULL DEFAULT CURRENT_DATE
        )
    ''')

    # Таблица платежей
    c.execute('''
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            payment_type TEXT NOT NULL,
            date TEXT NOT NULL DEFAULT CURRENT_DATE,
            menu_items TEXT DEFAULT '[]',
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')

    # Таблица выданной еды (кто что съел)
    c.execute('''
        CREATE TABLE IF NOT EXISTS meals (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            menu_id INTEGER NOT NULL,
            amount_received INTEGER NOT NULL,
            date TEXT NOT NULL DEFAULT CURRENT_DATE,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(menu_id) REFERENCES menu(id),
            UNIQUE(user_id, menu_id, date)
        )
    ''')

    # Заявки на продукты от поваров
    c.execute('''
        CREATE TABLE IF NOT EXISTS purchase_requests (
            id INTEGER PRIMARY KEY,
            cook_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            quantity REAL NOT NULL,
            unit TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TEXT NOT NULL DEFAULT CURRENT_DATE,
            FOREIGN KEY(cook_id) REFERENCES users(id)
        )
    ''')

    # Склад продуктов
    c.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY,
            product_name TEXT NOT NULL,
            quantity REAL NOT NULL DEFAULT 0.0,
            unit TEXT NOT NULL DEFAULT 'kg'
        )
    ''')

    # Отзывы
    c.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            menu_id INTEGER,
            rating INTEGER,
            average_rating REAL,
            comment TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_DATE
        )
    ''')

    admin_created = c.execute("SELECT EXISTS(SELECT 1 FROM users WHERE role = 'admin')").fetchone()[0]
    if admin_created == 0:
        c.execute("INSERT INTO users (username, email, password, user_balance, role, allergies) VALUES ('ServerAdministrator', ?, ?, 0.0, 'admin', 'none')", (os.getenv("ADMIN_EMAIL"), os.getenv("ADMIN_PASSWORD")))
    
    cook_created = c.execute("SELECT EXISTS(SELECT 1 FROM users WHERE role = 'cook')").fetchone()[0]
    if cook_created == 0:
        c.execute("INSERT INTO users (username, email, password, user_balance, role, allergies) VALUES ('Cook', ?, ?, 0.0, 'cook', 'none')", (os.getenv("COOK_EMAIL"), os.getenv("COOK_PASSWORD")))

    conn.commit()
    conn.close()

init_db()
