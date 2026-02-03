import sqlite3
from datetime import date

# Скрипт для студентов: меню, отзывы, получение еды
# Переводит формат дат python в понятный для sqlite формат
def adapt_date(val: date) -> str:
    return val.isoformat()

sqlite3.register_adapter(date, adapt_date)

current_date = date.today()

def view_menu(student_allergie):
    print(f"\n--- Меню на {current_date} ---")
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

        for item in items:
            meal_type, name, price, allergy = item
            print(f"[{meal_type}] {name} - {price} руб. (Аллергены: {allergy})")

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

def receive_meal(username, quantity):
    # Отмечаем, что забрали еду
    with sqlite3.connect('cafe.db') as conn:
        c = conn.cursor()
        
        # 1. Ищем студента
        c.execute("SELECT id FROM users WHERE username = ?", (username,))
        user_res = c.fetchone()
        if not user_res: 
            print("Студент не найден.")
            return
        user_id = user_res[0]

        # 2. Проверяем оплату
        c.execute("SELECT id FROM payments WHERE user_id = ? AND date = ?", (user_id, current_date))
        if not c.fetchone():
            print("Сначала нужно оплатить (или иметь абонемент)!")
            return

        # 3. Получаем корзину (список блюд)
        # Соответствует запросу пользователя: [id, type, name, price, allergy]
        c.execute("SELECT id, name FROM menu WHERE date = ?", (current_date,))
        basket = c.fetchall()
        
        if not basket:
            print("В меню сегодня пусто.")
            return
        
        print(f"\n--- Выдача еды для {username} ---")
        
        # 4. Проходим по каждому блюду из списка
        for item in basket:
            # Разбираем список как просил пользователь:
            menu_id = item[0]       # ID для БД
            # Название блюда
            dish_name = item[1]

            # Проверяем наличие продукта на складе
            c.execute("SELECT quantity FROM inventory WHERE product_name = ?", (dish_name,))
            inv_res = c.fetchone()
            
            if not inv_res or inv_res[0] < 1:
                print(f"ОШИБКА: {dish_name} закончился на складе!")
                continue
            try:
                # ВЫПОЛНЯЕМ ТРЕБУЕМЫЙ БЛОК КОДА ДЛЯ КАЖДОГО БЛЮДА:
                
                # Списываем продукт
                c.execute("UPDATE inventory SET quantity = quantity - ? WHERE product_name = ?", (dish_name, quantity))
                
                # Выдаем блюдо
                c.execute("INSERT INTO meals (user_id, menu_id, amount_received, date) VALUES (?, ?, ?, ?)", 
                        (user_id, menu_id, quantity, current_date))
                
                print(f"Выдано: {dish_name}")
                
            except sqlite3.IntegrityError:
                print(f"Блюдо '{dish_name}' вы уже получили сегодня.")
                # Если списание прошло, а выдача упала (уже ел) - возвращаем продукт
                c.execute("UPDATE inventory SET quantity = quantity + ? WHERE product_name = ?", (dish_name, quantity))
                conn.commit()

if __name__ == "__main__":
    pass

receive_meal('bomboclat julian linuxovich', 4)