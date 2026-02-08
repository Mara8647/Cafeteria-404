import sqlite3
from datetime import date

def adapt_date(val: date) -> str:
    return val.isoformat()

sqlite3.register_adapter(date, adapt_date)

current_date = date.today()

# Функции повара
def view_orders():
    print(f"\n--- Заказы на {current_date} ---")
    with sqlite3.connect('cafe.db') as conn:
        c = conn.cursor()
        
        # Кто уже получил еду
        print("\n--- Выданные порции ---")
        c.execute('''
            SELECT u.username, m.name
            FROM meals ml
            JOIN users u ON ml.user_id = u.id
            JOIN menu m ON ml.menu_id = m.id
            WHERE ml.date = ?
        ''', (current_date,))
        meals = c.fetchall()
        
        if not meals:
            print("Пока что не было выдано ни одной порции.")
        else:
            for m in meals:
                print(f"Студент {m[0]} получил {m[1]}")

def check_inventory():
    print(f"\n--- Склад продуктов ---")
    with sqlite3.connect('datab/cafe.db') as conn:
        c = conn.cursor()
        c.execute("SELECT product_name, quantity, unit FROM inventory")
        items = c.fetchall()

        if not items:
            print("Склад пуст.")
            return

        for item in items:
            name, quantity, unit = item
            print(f"{name}: {quantity} {unit}")

def update_inventory(product, change):
    with sqlite3.connect('cafe.db') as conn:
        c = conn.cursor()
        # Проверяем есть ли такой продукт
        c.execute("SELECT quantity FROM inventory WHERE product_name = ?", (product,))
        res = c.fetchone()
        
        if res:
            new_quantity = res[0] + change
            if new_quantity < 0:
                print("Остаток продуктов должен быть больше 0!")
                return
            c.execute("UPDATE inventory SET quantity = ? WHERE product_name = ?", (new_quantity, product))
            print(f"Остаток {product} обновлен: {new_quantity}")
        else:
            if change > 0:
                c.execute("INSERT INTO inventory (product_name, quantity) VALUES (?, ?)", (product, change))
                print(f"Новый продукт {product} добавлен: {change}")
            else:
                print("Такого продукта нет, списывать нечего.")

def create_purchase_request(cook_name, product, quantity):
    with sqlite3.connect('cafe.db') as conn:
        c = conn.cursor()
        
        # Ищем повара
        c.execute("SELECT id FROM users WHERE username = ?", (cook_name,))
        res = c.fetchone()
        if not res:
            print("Повар не найден в базе.")
            return
        
        cook_id = res[0]
        
        c.execute("INSERT INTO purchase_requests (cook_id, product_name, quantity, status) VALUES (?, ?, ?, 'pending')", 
                (cook_id, product, quantity))
        print(f"Заявка на {product} ({quantity}) успешно создана и ждет одобрения админа.")

# with sqlite3.connect('cafe.db') as conn:
#     cursor = conn.cursor()
#     cursor.execute(
#         "INSERT INTO menu (meal_type, name, price, allergies, date) VALUES('breakfast', 'Омлет', 150.0, 'eggs', ?)",
#         (date.today(),))
#     cursor.execute(
#         "INSERT INTO menu (meal_type, name, price, allergies, date) VALUES('lunch', 'Суп', 200.0, 'нет', ?)",
#         (date.today(),))
#     cursor.execute(
#         "INSERT INTO menu (meal_type, name, price, allergies, date) VALUES('lunch', 'Котлета с пюре', 200.0, 'нет', ?)",
#         (date.today(),))
#     cursor.execute(
#         "INSERT INTO menu (meal_type, name, price, allergies, date) VALUES('breakfast', 'что то ореховое', 200.0, 'nuts', ?)",
#         (date.today(),))

#     cursor.execute("INSERT INTO inventory (product_name, quantity, unit) VALUES ('Омлет', 10.0, 'portion')")
#     cursor.execute("INSERT INTO inventory (product_name, quantity, unit) VALUES ('Суп', 10.0, 'portion')")
#     cursor.execute("INSERT INTO inventory (product_name, quantity, unit) VALUES ('Котлета с пюре', 10.0, 'portion')")
#     cursor.execute("INSERT INTO inventory (product_name, quantity, unit) VALUES ('Котлета с пюре', 10.0, 'portion')")