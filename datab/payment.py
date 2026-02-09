import sqlite3
from datetime import date
import json


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

        # Собираем список оплаченных блюд для сохранения
        paid_dishes = []
        for item in items:
            # Структура item: [menu_id, meal_type, name, price, allergies] или [name, price, ...]
            dish_name = item[2]
            price = item[3]

            total_cost += price

            # Ищем menu_id по названию блюда
            c.execute("SELECT id FROM menu WHERE name = ? AND date = ?", (dish_name, current_date))
            menu_res = c.fetchone()
            menu_id = menu_res[0] if menu_res else None

            paid_dishes.append({
                "name": dish_name,
                "price": price,
                "menu_id": menu_id
            })

        # Сохраняем список блюд как JSON
        menu_items_json = json.dumps(paid_dishes)
        print(menu_items_json)

        if payment_type == 'subscription':
            # Если абонемент - списываем 0, но фиксируем факт
            c.execute("""
                INSERT INTO payments (user_id, amount, payment_type, date, menu_items) 
                VALUES (?, 0, ?, ?, ?)
            """, (user_id, payment_type, current_date, menu_items_json))
            print(f"Оплата по абонементу прошла успешно.")
            return True

        if total_cost <= balance:
            new_balance = balance - total_cost
            c.execute("UPDATE users SET user_balance = ? WHERE id = ?", (new_balance, user_id))
            c.execute("""
                INSERT INTO payments (user_id, amount, payment_type, date, menu_items) 
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, total_cost, payment_type, current_date, menu_items_json))
            return f"Успешно оплачено: {total_cost}руб. Остаток: {new_balance}руб."
        else:
            return f"Не достаточно средств! Требуется {total_cost}; ваш баланс {balance}."