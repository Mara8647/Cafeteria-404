import sqlite3
from datetime import date

# Переводит формат дат python в понятный для sqlite формат
def adapt_date(val: date) -> str:
    return val.isoformat()

sqlite3.register_adapter(date, adapt_date)

current_date = date.today()

# Оплата еды
def pay(username, items, payment_type):
    with sqlite3.connect('cafe.db') as conn:
        c = conn.cursor()

        # Данные пользователя
        c.execute("SELECT id, user_balance FROM users WHERE username = ?", (username,))
        user_data = c.fetchone()

        if not user_data:
            print("Такого пользователя нет.")
            return False

        user_id, balance = user_data
        total_cost = 0.0

        # Считаем сумму, пропуская то что нельзя есть
        for item in items:
            price = item[3]

            total_cost += price

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
            return f"Успешно оплачено: {total_cost}руб. Остаток: {new_balance}руб."
        else:
            return f"Не достаточно средств! Требуется {total_cost}; ваш баланс {balance}."
