import sqlite3

# Регистрация
def registration(username, email, password, role, allergies):
    with sqlite3.connect('cafe.db') as conn:
        c = conn.cursor()
        try:
            # Создаем пользователя, баланс пока 0
            c.execute("INSERT INTO users (username, email, password, payment_type, user_balance, role, allergies) VALUES (?, ?, ?, ?, 0.0, ?, ?)", 
                        (username, email, password, 'single', role, allergies))
            print(f"Пользователь {username} ({role}) успешно зарегистрирован!")
            return True
        except sqlite3.IntegrityError: 
            print("Ошибка: такой пользователь или email уже есть.")
            return False

# Вход в систему
def authorisation(username, password):
    with sqlite3.connect('cafe.db') as conn:
        c = conn.cursor()
        c.execute("SELECT id, role, allergies, payment_type, user_balance FROM users WHERE username = ? and password = ?", (username, password))
        user = c.fetchone()
        
        if user:
            return user
        else:
            print('Неверный логин или пароль.')
            return None

# Сменить тип оплаты (абонемент/разово)
def change_payment_type(username, password, new_type):
    user = authorisation(username, password)
    if user:
        with sqlite3.connect('cafe.db') as conn:
            c = conn.cursor()
            c.execute("UPDATE users SET payment_type = ? WHERE id = ?", (new_type, user[0]))
            print(f"Тип оплаты изменен на: {new_type}")

if __name__ == '__main__':
    # Для теста
    registration('test', 'test@test.com', '123', 'student', 'none')
    authorisation('test', '123')