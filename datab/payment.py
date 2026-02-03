import sqlite3
from datetime import date

# Переводит формат дат python в понятный для sqlite формат
def adapt_date(val: date) -> str:
    return val.isoformat()

sqlite3.register_adapter(date, adapt_date)

current_date = date.today()

# Оплата еды
def pay(username, quantity):
    with sqlite3.connect('cafe.db') as conn:
        c = conn.cursor()

        # Данные пользователя
        c.execute("SELECT id, payment_type, user_balance, allergies FROM users WHERE username = ?", (username,))
        user_data = c.fetchone()

        if not user_data:
            print("Такого пользователя нет.")
            return False

        user_id, payment_type, balance, user_allergy = user_data

        # Меню на сегодня
        if user_allergy != "none":
            c.execute("SELECT meal_type, name, price, allergies FROM menu WHERE date = ? AND allergies != ?", (current_date, user_allergy))
        else:
            c.execute("SELECT meal_type, name, price, allergies FROM menu WHERE date = ?", (current_date,))
        menu = c.fetchall()

        if not menu:
            print("Сегодня столовая не работает (меню нет).")
            return False

        total_cost = 0.0

        # Считаем сумму, пропуская то что нельзя есть
        for item in menu:
            price = item[2]

            total_cost += price * quantity

        if payment_type == 'subscription':
            # Если абонемент - списываем 0, но фиксируем факт
            c.execute("INSERT INTO payments (user_id, amount, payment_type, date) VALUES (?, 0, ?, ?)", 
                    (user_id, payment_type, current_date))
            print(f"Оплата по абонементу прошла успешно.")
            return True

        # Пробуем списать деньги (если не абонемент)
        if total_cost <= balance:
            new_balance = balance - total_cost
            c.execute("UPDATE users SET user_balance = ? WHERE id = ?", (new_balance, user_id))
            c.execute("INSERT INTO payments (user_id, amount, payment_type, date) VALUES (?, ?, ?, ?)", 
                    (user_id, total_cost, payment_type, current_date))
            print(f"Успешно оплачено: {total_cost}руб. Остаток: {new_balance}руб.")
            return True
        else:
            print(f"Не достаточно средств! Требуется {total_cost}; ваш баланс {balance}.")
            return False
        
pay('bomboclat julian linuxovich', 4)