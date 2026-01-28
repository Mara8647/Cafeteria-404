import os
import sqlite3
from datetime import date
import dbInitialisation
import login
import student
import cook
import admin
import payment

# Проверка всей системы после рефакторинга
def test_system():
    # 1. Сброс базы
    if os.path.exists('cafe.db'):
        os.remove('cafe.db')
    dbInitialisation.init_db()
    print("БД создана.")
    
    # заполняем меню
    with sqlite3.connect('cafe.db') as conn:
        conn.execute("INSERT INTO menu (meal_type, name, price, allergies, date) VALUES('breakfast', 'Omelette', 150.0, 'eggs', ?)", (date.today(),))
        conn.execute("INSERT INTO menu (meal_type, name, price, allergies, date) VALUES('lunch', 'Soup', 200.0, 'none', ?)", (date.today(),))
        
        # Заполняем склад, чтобы можно было поесть
        conn.execute("INSERT INTO inventory (product_name, quantity, unit) VALUES ('Omelette', 10.0, 'portion')")
        conn.execute("INSERT INTO inventory (product_name, quantity, unit) VALUES ('Soup', 10.0, 'portion')")

    # 2. Регистрация
    login.registration('student1', 's1@ya.ru', '123', 'student', 'none')
    login.registration('cook1', 'c1@ya.ru', '123', 'cook', 'none')
    
    # Дадим денег студенту
    with sqlite3.connect('cafe.db') as conn:
        conn.execute("UPDATE users SET user_balance = 1000.0 WHERE username='student1'")

    # 3. Студент
    print("\n--- TEST: Студент ---")
    student.view_menu()
    
    # Платим (импортируем функцию оплаты отдельно или через student если бы была обертка, но мы вызывали payment.pay напрямую в старом коде, 
    # а в новом 'human' коде я не делал обертку в student.py, но в задании просили 'wrapper' изначально.
    # В student.py сейчас нет pay. Импортируем из payment.
    payment.pay('student1', 1) # Суп (200) + Омлет (150) = 350
    
    student.receive_meal('student1')
    student.leave_review('student1', 'Soup', 5, 'Вкусно!')

    # 4. Повар
    print("\n--- TEST: Повар ---")
    cook.view_orders()
    cook.check_inventory()
    cook.create_purchase_request('cook1', 'Milk', 10)
    
    # 5. Админ
    print("\n--- TEST: Админ ---")
    # Надо достать ID заявки
    with sqlite3.connect('cafe.db') as conn:
        cur = conn.cursor()
        cur.execute("SELECT id FROM purchase_requests")
        rid = cur.fetchone()[0]
        
    admin.display_purchase_requests()
    admin.manage_request(rid, 'approve')
    
    cook.check_inventory() # Проверяем что молоко приехало
    admin.generate_report()

    # 6. Тестирование исключительных ситуаций
    print("\n--- TEST: Исключительные ситуации ---")
    
    # Кейс 1: Повторная отметка питания
    print(">> Проверка повторной выдачи:")
    student.receive_meal('student1') # Уже получал выше, должно выдать сообщение об ошибке (уже получено)
    
    # Кейс 2: Недостаточно средств
    print(">> Проверка нехватки средств:")
    login.registration('poor_student', 'poor@mail.ru', '123', 'student', 'none')
    # Баланс 0 по умолчанию
    res = payment.pay('poor_student', 1) 
    if not res:
        print("Верно: оплата не прошла (денег нет).")
    else:
        print("ОШИБКА: оплата прошла без денег!")
        
    # Кейс 3: Отсутствие продуктов
    print(">> Проверка отсутствия продуктов:")
    # Обнулим склад для Omelette (он есть в меню на сегодня)
    with sqlite3.connect('cafe.db') as conn:
        conn.execute("UPDATE inventory SET quantity = 0 WHERE product_name = 'Omelette'")
        conn.commit()
    
    # Дадим денег студенту, чтобы он ОПЛАТИЛ, но ЕДЫ НЕ БЫЛО
    with sqlite3.connect('cafe.db') as conn:
        conn.execute("UPDATE users SET user_balance = 1000 WHERE username='poor_student'")
    
    # Сначала оплата (она должна пройти, так как деньги есть)
    # Важно: В реальности оплата тоже может проверять наличие, но по ТЗ проверка выдачи отдельный пункт.
    # В payment.py нет проверки склада сейчас, только деньги.
    print("Оплата (деньги есть):")
    payment.pay('poor_student', 1)
    
    # Теперь пытаемся получить
    print("Попытка получить Омлет (которого нет на складе):")
    student.receive_meal('poor_student')

if __name__ == "__main__":
    test_system()
