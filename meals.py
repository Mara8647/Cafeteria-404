import sqlite3
from datetime import date

current_date = date.today()

# Переводит формат дат python в понятный для sqlite формат
def adapt_date(val: date) -> str:
    return val.isoformat()

sqlite3.register_adapter(date, adapt_date)

# Функция отвечающая за отметку о получении питания
def student_receive_meal(user_info, menu_id, amount_received):
    with sqlite3.connect('cafe.db') as connection:
        cursor = connection.cursor()
        if user_info:
            cursor.execute("INSERT INTO meals (user_id, menu_id, amount_received, date) VALUES (?, ?, ?, ?)", (user_info[0], menu_id, amount_received, current_date))

student_receive_meal([2], 2, 5)