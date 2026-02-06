import sqlite3


def registration(username, email, password, role, allergies):
    with sqlite3.connect('cafe.db') as connection:
        cursor = connection.cursor()
        try:
            cursor.execute("INSERT INTO users (username, email, password, payment_type, user_balance, role, allergies) VALUES (?, ?, ?, ?, ?, ?, ?)", (username, email, password, 'single', 0.0, role, allergies))
            print(f"{username} вы зарегистрированы как {role}")
            return True
        except sqlite3.IntegrityError as e:
            print(f"Ошибка: {e}")
            return False

def authorisation(username,password):
    with sqlite3.connect('cafe.db') as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT id, role FROM users WHERE username = ? and password = ?", (username, password) )
        user = cursor.fetchone()
        # Если юзер есть то приветственное сообщение , иначе отказ
        if user is not None:
            return user
        else:
            return None


def change_payment_type(new_payment_type):
    with sqlite3.connect('cafe.db') as connection:
        cursor = connection.cursor()
        cursor.execute("UPDATE users SET payment_type = ? WHERE id = ?", (new_payment_type, authorisation(username, password)[0]))


def check():
    with sqlite3.connect('./datab/cafe.db') as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM users")
        res = cursor.fetchall()
        for user in res:
            print(user)
