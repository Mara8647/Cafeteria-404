import sqlite3
from datetime import date

# Скрипт для студентов: меню, отзывы, получение еды
# Переводит формат дат python в понятный для sqlite формат
def adapt_date(val: date) -> str:
    return val.isoformat()

sqlite3.register_adapter(date, adapt_date)

current_date = date.today()

def view_menu(student_allergie):
    with sqlite3.connect('cafe.db') as conn:
        c = conn.cursor()
        if student_allergie != "none":
            c.execute("SELECT meal_type, name, price, allergies FROM menu WHERE date = ? AND allergies != ?", (current_date, student_allergie))
        else:
            c.execute("SELECT meal_type, name, price, allergies FROM menu WHERE date = ?", (current_date,))
        items = c.fetchall()

        if not items:
            print("На сегодня меню нет или оно не обновлено.")
            return

        return items

def leave_review(username, meal_name, rating, comment):
    # Тут по хорошему надо проверять авторизацию, но мы просто ищем пользователя по имени
    with sqlite3.connect('cafe.db') as conn:
        c = conn.cursor()
        c.execute("SELECT id FROM users WHERE username = ?", (username,))
        res = c.fetchone()
        if not res:
            print("Студент не найден.")
            return

        user_id = res[0]

        # Пытаемся найти блюдо по имени, чтобы привязать отзыв
        menu_id = None
        if meal_name:
            c.execute("SELECT id FROM menu WHERE name = ? AND date = ?", (meal_name, current_date))
            m_res = c.fetchone()
            if m_res:
                menu_id = m_res[0]

        try:
            c.execute("INSERT INTO reviews (user_id, menu_id, rating, comment) VALUES (?, ?, ?, ?)",
                    (user_id, menu_id, rating, comment))
            print("Спасибо за отзыв!")
        except Exception as e:
            print(f"Не удалось оставить отзыв: {e}")

def receive_meal(username, items):
    # Отмечаем, что забрали еду
    with sqlite3.connect('cafe.db') as conn:
        c = conn.cursor()
        # Ищем id пользователя
        c.execute("SELECT id FROM users WHERE username = ?", (username,))
        user_res = c.fetchone()
        if not user_res: return
        user_id = user_res[0]


        # Проверяем, оплачено ли питание сегодня
        c.execute("SELECT id FROM payments WHERE user_id = ? AND date = ?", (user_id, current_date))
        if not c.fetchone():
            print("Сначала нужно оплатить (или иметь абонемент)!")
            return

        # Отмечаем выдачу каждого блюда из меню
        for item in items:
            menu_id = item[0]
            dish_name = item[1]

            # Проверяем наличие на складе
            c.execute("SELECT quantity FROM inventory WHERE product_name = ?", (dish_name,))
            inventory_res = c.fetchone()
            
            if not inventory_res or inventory_res[0] < 1:
                print(f"ОШИБКА: Недостаточно продуктов для {dish_name}!")
                continue

            try:
                # Списываем продукт
                c.execute("UPDATE inventory SET quantity = quantity - 1 WHERE product_name = ?", (dish_name,))
                
                # Выдаем блюдо
                c.execute("INSERT INTO meals (user_id, menu_id, amount_received, date) VALUES (?, ?, 1, ?)", 
                        (user_id, menu_id, current_date))
                conn.commit() # Важно закоммитить списание
                print(f"Выдано блюдо: {dish_name}")
            except sqlite3.IntegrityError:
                print(f"Блюдо {dish_name} уже получено сегодня.")

                c.execute("UPDATE inventory SET quantity = quantity + 1 WHERE product_name = ?", (dish_name,))
                conn.commit()

if __name__ == "__main__":
    pass

view_menu("wheat, eggs")