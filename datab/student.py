import sqlite3
from datetime import date

# Регистрация адаптера для даты (чтобы date -> 'YYYY-MM-DD')
def adapt_date(val: date) -> str:
    return val.isoformat()

sqlite3.register_adapter(date, adapt_date)
current_date = date.today().isoformat()


def view_menu(student_allergie):
    with sqlite3.connect('cafe.db') as conn:
        c = conn.cursor()
        if student_allergie != "none":
            c.execute("SELECT meal_type, name, price, allergies FROM menu WHERE date = ? AND allergies != ?", (current_date, student_allergie))
        else:
            c.execute("SELECT meal_type, name, price, allergies FROM menu WHERE date = ?", (current_date,))
        items = c.fetchall()

        if not items:
            return []

        return items


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
    with sqlite3.connect('cafe.db') as conn:
        c = conn.cursor()
        c.execute("SELECT id FROM users WHERE username = ?", (username,))
        user_res = c.fetchone()
        if not user_res:
            return
        user_id = user_res[0]

        c.execute("SELECT id FROM payments WHERE user_id = ? AND date = ?", (user_id, current_date))
        if not c.fetchone():
            return

        for item in items:
            dish_name = item[1]
            c.execute("SELECT quantity FROM inventory WHERE product_name = ?", (dish_name,))
            inventory_res = c.fetchone()
            if not inventory_res or inventory_res[0] < 1:
                continue

            try:
                c.execute("UPDATE inventory SET quantity = quantity - 1 WHERE product_name = ?", (dish_name,))
                c.execute("INSERT INTO meals (user_id, menu_id, amount_received, date) VALUES (?, ?, 1, ?)",
                          (user_id, item[0], current_date))
                conn.commit()
            except sqlite3.IntegrityError:
                c.execute("UPDATE inventory SET quantity = quantity + 1 WHERE product_name = ?", (dish_name,))
                conn.commit()

if __name__ == "__main__":
    pass

