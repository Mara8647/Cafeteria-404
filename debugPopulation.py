# Это скрипт для вноса тестовых данных чтобы упростить проверку рабостоспособности остальных скрипптов

import sqlite3

with sqlite3.connect('cafe.db') as connection:
    cursor = connection.cursor()

    cursor.execute('''
        INSERT INTO users (username, email, password, payment_type, user_balance, role, allergies) VALUES('toki', 'test@cafe.com', '123', 'single', '50000000', 'student', 'milk')
 ''')
    cursor.execute('''
        INSERT INTO menu (meal_type, name, price, allergies, date) VALUES('breakfast', 'Омлет', 150, 'eggs', CURRENT_DATE);
''')
    cursor.execute('''
        INSERT INTO menu (meal_type, name, price, allergies, date) VALUES('lunch', 'Суп', 150, 'none', CURRENT_DATE);
''')