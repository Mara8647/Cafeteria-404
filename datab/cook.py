import sqlite3
from datetime import date
import json


def adapt_date(val: date) -> str:
    return val.isoformat()


sqlite3.register_adapter(date, adapt_date)
current_date = date.today().isoformat()  # Строка 'YYYY-MM-DD'


def view_orders():
    """Возвращает оплаченные, но не выданные заказы"""
    with sqlite3.connect('cafe.db') as conn:
        c = conn.cursor()

        # Получаем все оплаты с их блюдами
        c.execute('''
            SELECT p.user_id, u.username, p.menu_items
            FROM payments p
            JOIN users u ON p.user_id = u.id
            WHERE p.date = ?
            AND u.role = 'student'
        ''', (current_date,))

        payments = c.fetchall()

        result = []

        for user_id, username, menu_items_json in payments:
            if not menu_items_json or menu_items_json == '[]':
                continue

            try:
                menu_items = json.loads(menu_items_json)

                for item in menu_items:
                    dish_name = item.get('name')
                    menu_id = item.get('menu_id')

                    if not menu_id:
                        # Если нет menu_id в данных, ищем по имени
                        c.execute('''
                            SELECT id FROM menu 
                            WHERE name = ? AND date = ?
                        ''', (dish_name, current_date))
                        menu_res = c.fetchone()
                        if not menu_res:
                            continue
                        menu_id = menu_res[0]

                    # Проверяем, выдано ли уже это блюдо
                    c.execute('''
                        SELECT 1 FROM meals 
                        WHERE user_id = ? AND menu_id = ? AND date = ?
                    ''', (user_id, menu_id, current_date))

                    if not c.fetchone():  # Блюдо не выдано
                        result.append((username, dish_name, menu_id))
            except (json.JSONDecodeError, TypeError):
                continue

        return result


def mark_meal_delivered(username, menu_id):
    with sqlite3.connect('cafe.db') as conn:
        c = conn.cursor()

        # Найти user_id
        c.execute("SELECT id FROM users WHERE username = ?", (username,))
        user_res = c.fetchone()
        if not user_res:
            raise ValueError("Пользователь не найден")

        user_id = user_res[0]

        # Проверить, оплачено ли блюдо
        c.execute("""
            SELECT p.menu_items
            FROM payments p
            WHERE p.user_id = ? AND p.date = ?
        """, (user_id, current_date))

        payment_res = c.fetchone()
        if not payment_res or not payment_res[0]:
            raise ValueError("Заказ не оплачен")

        # Проверить, не выдано ли уже
        c.execute("""
            SELECT 1 FROM meals 
            WHERE user_id = ? AND menu_id = ? AND date = ?
        """, (user_id, menu_id, current_date))

        if c.fetchone():
            raise ValueError("Блюдо уже выдано")

        c.execute("""
            INSERT INTO meals (user_id, menu_id, amount_received, date) 
            VALUES (?, ?, 1, ?)
        """, (user_id, menu_id, current_date))

        return True


def check_inventory():
    """Возвращает данные о складе"""
    with sqlite3.connect('cafe.db') as conn:
        c = conn.cursor()
        c.execute("SELECT product_name, quantity, unit FROM inventory ORDER BY product_name")
        return c.fetchall()


def update_inventory(product, change):
    """Обновляет количество продукта на складе"""
    with sqlite3.connect('cafe.db') as conn:
        c = conn.cursor()

        # Проверяем есть ли такой продукт
        c.execute("SELECT quantity FROM inventory WHERE product_name = ?", (product,))
        res = c.fetchone()

        if res:
            new_quantity = res[0] + change
            if new_quantity < 0:
                raise ValueError("Остаток продуктов не может быть отрицательным!")

            c.execute("UPDATE inventory SET quantity = ? WHERE product_name = ?",
                      (new_quantity, product))
            return f"Остаток {product} обновлен: {new_quantity}"
        else:
            if change > 0:
                c.execute("INSERT INTO inventory (product_name, quantity, unit) VALUES (?, ?, 'portion')",
                          (product, change))
                return f"Новый продукт {product} добавлен: {change}"
            else:
                raise ValueError("Такого продукта нет, списывать нечего.")


def create_purchase_request(cook_name, product, quantity):
    """Создает заявку на закупку"""
    with sqlite3.connect('cafe.db') as conn:
        c = conn.cursor()

        # Ищем повара
        c.execute("SELECT id FROM users WHERE username = ?", (cook_name,))
        res = c.fetchone()
        if not res:
            raise ValueError("Повар не найден в базе.")

        cook_id = res[0]

        c.execute("""
            INSERT INTO purchase_requests (cook_id, product_name, quantity, status) 
            VALUES (?, ?, ?, 'pending')
        """, (cook_id, product, quantity))

        return f"Заявка на {product} ({quantity}) успешно создана и ждет одобрения админа."


def clear_orders():
    """Удаляет все записи из payments и meals за текущую дату"""
    with sqlite3.connect('cafe.db') as conn:
        c = conn.cursor()

        # Удаляем записи из meals
        c.execute("DELETE FROM meals WHERE date = ?", (current_date,))

        # Удаляем записи из payments
        c.execute("DELETE FROM payments WHERE date = ?", (current_date,))

        count = c.rowcount
        return count


def init_test_data():
    # Тестовые данные
    with sqlite3.connect('cafe.db') as conn:
        cursor = conn.cursor()

        # Добавляем тестовое меню
        cursor.execute("""
            INSERT INTO menu (meal_type, name, price, allergies, date) 
            VALUES('breakfast', 'Омлет', 150.0, 'eggs', ?)
        """, (date.today(),))

        cursor.execute("""
            INSERT INTO menu (meal_type, name, price, allergies, date) 
            VALUES('lunch', 'Суп', 200.0, 'нет', ?)
        """, (date.today(),))

        cursor.execute("""
            INSERT INTO menu (meal_type, name, price, allergies, date) 
            VALUES('lunch', 'Котлета с пюре', 200.0, 'нет', ?)
        """, (date.today(),))

        # Добавляем инвентарь
        cursor.execute("""
            INSERT INTO inventory (product_name, quantity, unit) 
            VALUES ('Омлет', 10.0, 'порц.')
        """)

        cursor.execute("""
            INSERT INTO inventory (product_name, quantity, unit) 
            VALUES ('Суп', 10.0, 'порц.')
        """)

        cursor.execute("""
            INSERT INTO inventory (product_name, quantity, unit) 
            VALUES ('Котлета с пюре', 10.0, 'порц.')
        """)
