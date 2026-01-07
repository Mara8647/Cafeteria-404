import sqlite3
from datetime import date

um = 'toki'
current_date = date.today()

# Переводит формат дат python в понятный для sqlite формат
def adapt_date(val: date) -> str:
    return val.isoformat()

sqlite3.register_adapter(date, adapt_date)

# Функция отвечающая за оплату
def pay(username, amount_of_meals):
    with sqlite3.connect('cafe.db', detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES) as connection:
        cursor = connection.cursor()

        # Собираем id, способ оплаты и аллергию пользователя
        cursor.execute("SELECT id, payment_type, user_balance, allergies FROM users WHERE username = ?", (username,))
        user_data = cursor.fetchone()
        
        # Собираем информацию о сегодняшнем меню
        cursor.execute("SELECT meal_type, name, price, allergies FROM menu WHERE date = ?", (current_date,))
        menu_items = cursor.fetchall()

        amount_to_pay = 0.0
        # Проверяем еду на наличие аллергенов
        for menu_item in menu_items:
            if menu_item[3] != user_data[3]:
                amount_to_pay += menu_item[2] * amount_of_meals
            else:
                print(f"{menu_item[0]} содержит аллергены.")
            
        # Проверяем баланс пользвателя
        if amount_to_pay <= user_data[2]:
            cursor.execute("UPDATE users SET user_balance = ? WHERE id = ?", (user_data[2] - amount_to_pay, user_data[0]))
            cursor.execute("INSERT INTO payments (user_id, amount, payment_type, date) VALUES (?, ?, ?, ?)", (user_data[0], amount_to_pay, user_data[1], current_date))
            print(f"Оплата прошла успешно. Ваш баланс: {user_data[2] - amount_to_pay}")
        else:
            print("У вас недостаточно средств")


pay(um, 3)