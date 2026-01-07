import sqlite3
from datetime import date

# Переводит формат дат python в понятный для sqlite формат
def adapt_date(val: date) -> str:
    return val.isoformat()

sqlite3.register_adapter(date, adapt_date)

current_date = date.today()

um = input()
pw = input()
npt = input()

# Функция отвечающая за регистрацию 
def registration(username, email, password, payment_type, role, allergies):
    with sqlite3.connect('cafe.db') as connection:
            cursor = connection.cursor()
            #Выполняется запрос на регистрацию
            try:                    
                cursor.execute("INSERT INTO users (username, email, password, payment_type, user_balance, role, allergies) VALUES (?, ?, ?, ?, 0.0, ?, ?)", (username, email, password, payment_type, role, allergies) )
                print(f"{username} вы зарегистрированы как {role}")
            except sqlite3.IntegrityError:  #Если пользователь уже существует выводим "ошибку" !!!Только для случая когда IntegrityError!!!
                print("Такой пользователь уже существует")

# Функция отвечающая за авторизацию юзера 
def authorisation(username,password):
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
# def student_Receive_meal(menu_id):
#     with sqlite3.connect('cafe.db') as connection:
#         cursor = connection.cursor()
#         cursor.execute("INSERT INTO meals (user_id, menu_id, date) VALUES (?, ?, ?)", (authorisation(um, pw)[0], menu_id, current_date))

change_payment_type(npt)