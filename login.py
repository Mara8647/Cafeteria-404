import sqlite3
from datetime import date

# Переводит формат дат python в понятный для sqlite формат
def adapt_date(val: date) -> str:
    return val.isoformat()

sqlite3.register_adapter(date, adapt_date)

current_date = date.today()

um = 'toki'
pw = '123'

# Функция отвечающая за регистрацию 
def registration(username, email, password, role, allergies):
    with sqlite3.connect('cafe.db') as connection:
            cursor = connection.cursor()
            #Выполняется запрос на регистрацию
            try:                    
                cursor.execute("INSERT INTO users (username, email, password, payment_type, user_balance, role, allergies) VALUES (?, ?, ?, ?, 0.0, ?, ?)", (username, email, password, 'single', role, allergies) )
                print(f"{username} вы зарегистрированы как {role}")
            except sqlite3.IntegrityError as e:  #Если пользователь уже существует выводим "ошибку" !!!Только для случая когда IntegrityError!!!
                print(f"Ошибка: {e}")

# Функция отвечающая за авторизацию юзера 
def authorisation(username, password):
    with sqlite3.connect('cafe.db') as connection:
        cursor = connection.cursor()
        #Выполняется запрос на авторизацию
        cursor.execute("SELECT id, role FROM users WHERE username = ? and password = ?", (username, password) )
        user = cursor.fetchone()
        # Если юзер есть то приветственное сообщение , иначе отказ
        if user is not None:
            print(f'Добрый день, {username}' )
            return user
        else:
            print(f'Во входе отказано')
            return None
       #P.S. возвращаем user для последующей проверки выдачи питания и проверки роли пользователя (по id и role)

# Функция отвечающая за изменение способа оплаты
def change_payment_type(new_payment_type):
     with sqlite3.connect('cafe.db') as connection:
        cursor = connection.cursor()
        cursor.execute("UPDATE users SET payment_type = ? WHERE id = ?", (new_payment_type, authorisation(um, pw)[0]))

# Функция отвечающая за отметку о получении питания
def student_Receive_meal(amount_payed, amount_received):
    if amount_payed >= amount_received and amount_received >= 0:
        with sqlite3.connect('cafe.db') as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT id FROM menu WHERE date = ?", (current_date,))
            menu_id = cursor.fetchone()
            cursor.execute("INSERT INTO meals (user_id, menu_id, amount_received, date) VALUES (?, ?, ?, ?)", (authorisation(um, pw)[0], menu_id[0], amount_received, current_date))
    else:
        print("Введено некорректное количество полученных блюд")


student_Receive_meal(3, 3)