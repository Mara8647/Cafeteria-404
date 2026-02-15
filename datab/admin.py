import sqlite3
from datetime import date

# Переводит формат дат python в понятный для sqlite формат
def adapt_date(val: date) -> str:
    return val.isoformat()

sqlite3.register_adapter(date, adapt_date)

current_date = date.today()

# Функции админа
def view_statistics():
    print(f"\n=== Статистика на {current_date} ===")
    with sqlite3.connect('cafe.db') as conn:
        c = conn.cursor()

        # Считаем деньги
        c.execute("SELECT SUM(amount) FROM payments WHERE date = ?", (current_date,))
        res = c.fetchone()
        income = res[0] if res[0] else 0.0
        print(f"Касса сегодня: {income} руб.")
        # Считаем порции
        c.execute("SELECT COUNT(*) FROM meals WHERE date = ?", (current_date,))
        res = c.fetchone()
        count = res[0] if res[0] else 0
        print(f"Выдано блюд: {count}")

def display_purchase_requests():
    print(f"\n=== Заявки на продукты ===")
    with sqlite3.connect('cafe.db') as conn:
        c = conn.cursor()
        c.execute("SELECT id, product_name, quantity, status, created_at FROM purchase_requests WHERE status = 'pending'")
        reqs = c.fetchall()

        if not reqs:
            print("Заявки отсутствуют.")
        else:
            for r in reqs:
                print(f"#{r[0]} | {r[1]} ({r[2]}) | от {r[4]}")

def manage_request(request_id, action):
    # action: 'approve' (добро) или 'reject' (отказ)
    if action not in ('approve', 'reject'):
        print("Ошибка. Выбрано некорректное действие (принимается 'approve' или 'reject').")
        return

    status = 'approved' if action == 'approve' else 'rejected'

    with sqlite3.connect('cafe.db') as conn:
        c = conn.cursor()

        # Ищем заявку
        c.execute("SELECT product_name, quantity, unit FROM purchase_requests WHERE id = ? AND status = 'pending'", (request_id,))
        request = c.fetchone()
        if not request:
            print("Такой заявки не существует.")
            return
        # Меняем статус
        c.execute("UPDATE purchase_requests SET status = ? WHERE id = ?", (status, request_id))
        print(f"Заявка #{request_id} -> {status}")
        # Если одобрили - добавляем на склад
        if status == 'approved':
            product, quantity, unit = request
            # Проверяем был ли уже такой товар
            c.execute("SELECT quantity FROM inventory WHERE product_name = ?", (product,))
            inventory = c.fetchone()
            if inventory:
                new_quantity = inventory[0] + quantity
                c.execute("UPDATE inventory SET quantity = ? WHERE product_name = ?", (new_quantity, product))
            else:
                c.execute("INSERT INTO inventory (product_name, quantity, unit) VALUES (?, ?, ?)", (product, quantity, unit))
            print(f"На склад добавлено: {product} (+{quantity})")

def generate_report():
    print("\n-------------------------")
    print("      ДНЕВНОЙ ОТЧЕТ      ")
    print("-------------------------")
    view_statistics()
    print("-------------------------")
