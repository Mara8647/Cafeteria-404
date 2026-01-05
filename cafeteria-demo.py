import sqlite3

def init_db():
    #создание связи с БД (создается файл cafe в котором будут храниться данные)"
    connection = sqlite3.connect('cafe')
    #создаем указатель для отправки SQL запросы в БД и получения результатов"
    сursor = connection.cursor()
    #Таблица для юзеров
    сursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('student', 'cook', 'admin')),
                allergies TEXT
            )
        ''')
    #Таблица для меню на каждый день
    сursor.execute('''
            CREATE TABLE IF NOT EXISTS menu (
                id INTEGER PRIMARY KEY,
                meal_type TEXT NOT NULL CHECK(meal_type IN ('breakfast', 'lunch')),
                name TEXT NOT NULL,
                price REAL NOT NULL,
                date TEXT NOT NULL
            )
        ''')
    #Таблица для оплат
    сursor.execute('''
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                payment_type TEXT NOT NULL CHECK(payment_type IN ('single', 'subscription')),
                date TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        ''')
    #Таблица для подсчета кому что выдано и в каком
    сursor.execute('''
            CREATE TABLE IF NOT EXISTS meals (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                menu_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id),
                FOREIGN KEY(menu_id) REFERENCES menu(id),
                UNIQUE(user_id, menu_id, date)
            )
        ''')
    #Таблица дляз апросов на покупку
    сursor.execute('''
            CREATE TABLE IF NOT EXISTS purchase_requests (
                id INTEGER PRIMARY KEY,
                cook_id INTEGER NOT NULL,
                product_name TEXT NOT NULL,
                quantity REAL NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending', 'approved', 'rejected')),
                created_at TEXT NOT NULL,
                FOREIGN KEY(cook_id) REFERENCES users(id)
            )
        ''')
    
# Функция отвечающая за регистрацию 
def registration(username,password,role,allergies = "НЕТ"):
    with sqlite3.connect('cafe') as connection:
            cursor = connection.cursor()
            #Выполняется запрос на регистрацию
            try:                    
                cursor.execute("INSERT INTO users (username, password, role, allergies) VALUES (?, ?, ?, ?)" , (username, password, role, allergies) )
                print(f"{username} вы зарегистрированы как {role}")
            except sqlite3.IntegrityError:  #При уже существовании данного юзера выводим "ошибку" !!!только для случая когда IntegrityError!!!
                print("Такой пользователь уже существует")

# Функция отвечающая за авторизацию юзера 
def authorisation(username,password):
    with sqlite3.connect('cafe') as connection:
        cursor = connection.cursor()
        #Выполняется запрос на авторизацию
        cursor.execute("SELECT id, role FROM users WHERE username = ? and password = ?" , (username , password) )
        user = cursor.fetchone()
        # Если юзер есть то приветственное сообщение , иначе отказ
        if user is not None:
            print(f'Добрый день , {user}' )
            return user
        else:
            print(f'Во входе отказано')
            return None
       #P.S. возвращаем user для последующей проверки выдачи питания и проверки роли пользователя (по id и role)
     


# Запуск инициализации при прямом вызове скрипта
if __name__ == '__main__':
    init_db()