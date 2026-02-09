import sqlite3
from datetime import date

# Регистрация адаптера для даты (чтобы date -> 'YYYY-MM-DD')
def adapt_date(val: date) -> str:
    return val.isoformat()

sqlite3.register_adapter(date, adapt_date)
current_date = date.today().isoformat()


def view_menu(student_allergie):
    print(student_allergie)
    with sqlite3.connect('cafe.db') as conn:
        c = conn.cursor()
        c.execute("SELECT id, meal_type, name, price, allergies FROM menu WHERE date = ?", (current_date,))
        items = c.fetchall()

    if student_allergie and student_allergie != "none":
        user_allergens = {a.strip() for a in student_allergie.split(',')}

        filtered_items = []
        for item in items:
            allergies = item[4]

            if allergies == 'none':
                filtered_items.append(item)
                continue

            dish_allergens = {a.strip() for a in allergies.split(',')}

            if not (user_allergens & dish_allergens):
                filtered_items.append(item)

        items = filtered_items

    return items if items else []


def leave_review(username, meal_name, rating, comment):
    with sqlite3.connect('cafe.db') as conn:
        c = conn.cursor()
        c.execute("SELECT id FROM users WHERE username = ?", (username,))
        res = c.fetchone()
        if not res:
            return False

        user_id = res[0]

        # Находим menu_id по имени и дате
        c.execute("SELECT id FROM menu WHERE name = ? AND date = ?", (meal_name, current_date))
        m_res = c.fetchone()
        menu_id = m_res[0] if m_res else None

        try:
            c.execute("INSERT INTO reviews (user_id, menu_id, rating, comment) VALUES (?, ?, ?, ?)",
                    (user_id, menu_id, rating, comment))
            return True
        except Exception as e:
            return False


def receive_meal(username, items):
    # Отмечаем, что забрали еду
    with sqlite3.connect('cafe.db') as conn:
        c = conn.cursor()
        # Ищем id пользователя
        c.execute("SELECT id FROM users WHERE username = ?", (username,))
        user_res = c.fetchone()
        if not user_res: return
        user_id = user_res[0]


        c.execute("SELECT id FROM payments WHERE user_id = ? AND date = ?", (user_id, current_date))
        if not c.fetchone():
            print("Сначала нужно оплатить (или иметь абонемент)!")
            return

        # Отмечаем выдачу каждого блюда из меню
        for item in items:
            # item может быть [menu_id, dish_name] или [cat, name, price, allergen]
            if isinstance(item[0], int):  # если первый элемент — id
                menu_id = item[0]
                dish_name = item[1]
            else:
                dish_name = item[1]
                # Найти menu_id по имени
                c.execute("SELECT id FROM menu WHERE name = ? AND date = ?", (dish_name, current_date))
                res = c.fetchone()
                if not res:
                    print(f"Блюдо '{dish_name}' не найдено в меню.")
                    continue
                menu_id = res[0]


            c.execute("SELECT quantity FROM inventory WHERE product_name = ?", (dish_name,))
            inventory_res = c.fetchone()
            if not inventory_res or inventory_res[0] < 1:
                print(f"ОШИБКА: Недостаточно продуктов для {dish_name}!")
                continue

            try:

                c.execute("UPDATE inventory SET quantity = quantity - 1 WHERE product_name = ?", (dish_name,))

                # Выдаем блюдо
                c.execute("INSERT INTO meals (user_id, menu_id, amount_received, date) VALUES (?, ?, 1, ?)",
                        (user_id, menu_id, current_date))
                conn.commit()  # Важно закоммитить
                print(f"Выдано блюдо: {dish_name}")
            except sqlite3.IntegrityError:
                print(f"Блюдо {dish_name} уже получено сегодня.")
                c.execute("UPDATE inventory SET quantity = quantity + 1 WHERE product_name = ?", (dish_name,))
                conn.commit()

if __name__ == "__main__":
    pass
