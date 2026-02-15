import sqlite3
import os
from flask import Flask, request, redirect, render_template, url_for, jsonify, session
from datab import login, payment, student, dbInitialisation, admin
from datab.cook import check_inventory,create_purchase_request, update_inventory, view_orders, mark_meal_delivered, init_test_data
import datetime

dbInitialisation.init_db()
init_test_data()

current_date = datetime.date.today().isoformat()

app = Flask(__name__, template_folder='./templates')
app.secret_key = 'secret_key_123412'



def get_current_user():
    user_id = session.get('user_id')
    if not user_id:
        return None
    with sqlite3.connect('cafe.db') as conn:
        cursor = conn.cursor()
        row = cursor.execute("SELECT id, username, role FROM users WHERE id = ?", (user_id,)).fetchone()
        if row:
            return {'id': row[0], 'username': row[1], 'role': row[2]}
    return None


# === Главная страница ===
@app.route('/', methods=['GET'])
def first_page():
    return render_template('first_page.html')


# === Вход ===
@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        # Проверяем учётные данные
        user = login.authorisation(username=username, password=password)
        if user:
            session['user_id'] = user[0]
            print(f"{user}")
            print(f"Пользователь {username} успешно авторизован")
            return redirect(url_for('main_page'))
        else:
            print("Неверный логин или пароль")
            return render_template('login_page.html', error="Неверный логин или пароль")

    return render_template('login_page.html')


# === Регистрация ===
@app.route('/register', methods=['GET', 'POST'])
def register_page():
    if request.method == 'POST':
        role = request.form.get('role', 'student')
        username = request.form.get('name', '')
        email = request.form.get('email', '')
        password = request.form.get('password', '')
        allergies = request.form.get('allergens', '') or 'none'

        login.registration(username, email, password, role, allergies)

        with sqlite3.connect('cafe.db') as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            user_id = cursor.fetchone()[0]

        session['user_id'] = user_id
        return redirect(url_for('main_page'))

    return render_template('register_page.html')


# === Главная страница (после входа) ===
@app.route('/main', methods=['GET'])
def main_page():
    user = get_current_user()
    if not user:
        return redirect(url_for('login_page'))

    with sqlite3.connect('cafe.db') as conn:
        cursor = conn.cursor()
        balance_row = cursor.execute("SELECT user_balance FROM users WHERE id = ?", (user['id'],)).fetchone()
        balance = balance_row[0] if balance_row else 0

    if user['role'] == 'student':
        return render_template('main_page_student.html', username=user['username'], balance=balance)
    elif user['role'] == 'cook':
        return render_template('main_page_cook.html', username=user['username'])
    elif user['role'] == 'admin':
    # Подключаемся к базе данных
        with sqlite3.connect('cafe.db') as conn:
            cursor = conn.cursor()
        
            # Получаем статистику на сегодня 
            cursor.execute("SELECT SUM(amount) FROM payments WHERE date = date('now')")
            income_result = cursor.fetchone()
            income = income_result[0] if income_result[0] else 0.0
        
            cursor.execute("SELECT COUNT(*) FROM meals WHERE date = date('now')")
            count_result = cursor.fetchone()
            count = count_result[0] if count_result[0] else 0
        
            # Получаем количество pending заявок
            cursor.execute("SELECT COUNT(*) FROM purchase_requests WHERE status = 'pending'")
            pending_result = cursor.fetchone()
            pending_count = pending_result[0] if pending_result[0] else 0 
    
        # Передаем все данные в шаблон
        return render_template('main_page_admin.html', 
                                username=user['username'],
                                income=income,
                                count=count,
                                pending_count=pending_count,  # ← НОВАЯ ПЕРЕМЕННАЯ
                                current_date=current_date)
    else:
        return redirect(url_for('login_page'))


# === API: Получить меню для текущего пользователя ===
@app.route('/api/menu', methods=['GET'])
def menu():
    user = get_current_user()
    if not user:
        return jsonify([]), 401

    with sqlite3.connect('cafe.db') as conn:
        cursor = conn.cursor()
        row = cursor.execute("SELECT allergies FROM users WHERE id = ?", (user['id'],)).fetchone()
        allergies = row[0] if row else 'none'

    menu_items = student.view_menu(allergies)

    enhanced_menu = []
    for item in menu_items:
        dish_name = item[2]
        with sqlite3.connect('cafe.db') as conn:
            c = conn.cursor()
            c.execute("""
                SELECT AVG(rating) as avg_rating, COUNT(*) as count
                FROM reviews
                WHERE menu_id = (SELECT id FROM menu WHERE name = ? AND date = ?)
            """, (dish_name, student.current_date))
            row = c.fetchone()
            avg_rating = round(row[0], 1) if row[0] else 0
            review_count = row[1] if row[1] else 0

        enhanced_item = list(item) + [avg_rating, review_count]  # добавляем [avg, count]
        enhanced_menu.append(enhanced_item)

    return jsonify(enhanced_menu)


# === API: Создать заказ ===
@app.route('/api/order', methods=['POST'])
def create_order():
    user = get_current_user()
    if not user:
        return jsonify({"error": "Не авторизован"}), 401

    data = request.get_json()
    items = data.get('items', [])
    total = data.get('total', 0)
    payment_type = data.get('type', '')

    with sqlite3.connect('cafe.db') as conn:
        cursor = conn.cursor()
        balance = cursor.execute("SELECT user_balance FROM users WHERE id = ?", (user['id'],)).fetchone()[0]

    # Сохраняем заказ и оплату а так же списываем продукты со склада
    status = payment.pay(user['username'], items, payment_type)

    if status == True or "Успешно" in str(status):
        return jsonify({
            "new_balance": balance - total,
            "status": "Оплата прошла успешно",
            "total": total
        })
    else:
        return jsonify({"error": status}), 400


# === API: Оставить отзыв ===
@app.route('/api/review', methods=['POST'])
def api_leave_review():
    user = get_current_user()
    if not user:
        return jsonify({"error": "Не авторизован"}), 401

    data = request.get_json()
    meal_name = data.get('dish_name')
    rating = data.get('rating')
    comment = data.get('comment', '').strip()

    success = student.leave_review(username=user['username'], meal_name=meal_name, rating=rating, comment=comment)

    if success:
        return jsonify({"status": "ok"})
    else:
        return jsonify({"error": "Не удалось сохранить отзыв"}), 500


@app.route('/api/reviews', methods=['GET'])
def get_reviews():
    dish_name = request.args.get('dish')
    if not dish_name:
        return jsonify([])

    with sqlite3.connect('cafe.db') as conn:
        c = conn.cursor()
        c.execute("""
            SELECT u.username, r.rating, r.comment, r.created_at
            FROM reviews r
            JOIN users u ON u.id = r.user_id
            JOIN menu m ON m.id = r.menu_id
            WHERE m.name = ? AND m.date = ?
            ORDER BY r.created_at DESC
        """, (dish_name, student.current_date))
        reviews = [
            {"username": row[0], "rating": row[1], "comment": row[2] or "Без комментария", "date": row[3]}
            for row in c.fetchall()
        ]
        return jsonify(reviews)


@app.route('/api/updateBalance', methods=['POST'])
def api_updateBalance():
    user = get_current_user()
    if not user:
        return "Не авторизован", 401

    balance = request.form.get('amount')
    if not balance:
        return "Сумма не указана", 400

    try:
        balance = float(balance)
        if balance <= 0:
            return "Сумма должна быть положительной", 400
    except ValueError:
        return "Некорректная сумма", 400

    with sqlite3.connect('cafe.db') as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET user_balance = user_balance + ? WHERE id = ?", (balance, user['id']))
        conn.commit()

    return redirect(url_for('main_page'))

@app.route('/api/handle_request', methods=['POST'])
def handle_request():
    user = get_current_user()
    if not user or user['role'] != 'admin':
        return jsonify({"error": "Не авторизован"}), 401
    
    data = request.get_json()
    request_id = data.get('request_id')
    action = data.get('action')  # 'approve' или 'reject'
    
    if not request_id or action not in ['approve', 'reject']:
        return jsonify({"error": "Неверные данные"}), 400
    
    try:
        admin.manage_request(request_id, action)
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# -- Получить заявки на покупку --
@app.route('/api/purchase_requests', methods=['GET'])
def get_purchase_requests():
    user = get_current_user()
    if not user or user['role'] != 'admin':
        return jsonify({"error": "Не авторизован"}), 401

    with sqlite3.connect('cafe.db') as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, cook_id, product_name, quantity, unit, status, created_at 
            FROM purchase_requests 
            WHERE status = 'pending'
            ORDER BY created_at DESC
        """)
        
        requests = []
        for row in cursor.fetchall():
            requests.append({
                "id": row[0],
                "cook_id": row[1],
                "product_name": row[2],
                "quantity": row[3],
                "unit" : row[4],
                "status": row[5],
                "created_at": row[6]
            })
    
    return jsonify(requests)

# -- Статистика за неделю (для графика) --
@app.route('/api/weekly_stats', methods=['GET'])
def get_weekly_stats():
    user = get_current_user()
    if not user or user['role'] != 'admin':
        return jsonify({"error": "Не авторизован"}), 401
    
    with sqlite3.connect('cafe.db') as conn:
        cursor = conn.cursor()
        
        # Получаем статистику за последние 7 дней
        cursor.execute("""
            SELECT 
                date,
                COALESCE(SUM(amount), 0) as daily_income,
                COALESCE((SELECT COUNT(*) FROM meals WHERE date = payments.date), 0) as daily_meals
            FROM payments 
            WHERE date >= date('now', '-6 days')
            GROUP BY date
            ORDER BY date
        """)
        
        # Получаем все данные сразу
        db_data = cursor.fetchall()
        
        # Создаем словарь для быстрого поиска по дате
        db_dict = {}
        for row in db_data:
            db_dict[row[0]] = {
                "income": float(row[1]),
                "meals": row[2]
            }
        
        # Создаем структуру для всех дней недели
        weekly_data = []
        import datetime
        
        # Генерируем даты за последние 7 дней
        today = datetime.date.today()
        for i in range(6, -1, -1):  # от 6 дней назад до сегодня
            day = today - datetime.timedelta(days=i)
            day_str = day.isoformat()
            
            # Получаем данные для этого дня или используем нули
            if day_str in db_dict:
                day_data = {
                    "date": day_str,
                    "income": db_dict[day_str]["income"],
                    "meals": db_dict[day_str]["meals"]
                }
            else:
                day_data = {
                    "date": day_str,
                    "income": 0.0,
                    "meals": 0
                }
            
            # Добавляем название дня недели
            day_names = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
            day_data["day_name"] = day_names[day.weekday()]
            
            weekly_data.append(day_data)
    
    return jsonify(weekly_data)

# === API для повара ===

@app.route('/api/cook/orders', methods=['GET'])
def api_view_orders():
    user = get_current_user()
    if not user or user['role'] != 'cook':
        return jsonify({"error": "Доступ запрещён"}), 403

    meals = view_orders()

    orders = [{"student": m[0], "dish": m[1], "menu_id": m[2]} for m in meals]
    return jsonify(orders)


@app.route('/api/cook/inventory', methods=['GET'])
def api_check_inventory():
    user = get_current_user()
    if not user or user['role'] != 'cook':
        return jsonify({"error": "Доступ запрещён"}), 403

    items = check_inventory()

    inventory = [{"product": i[0], "quantity": i[1], "unit": i[2] or "порц."} for i in items]
    return jsonify(inventory)


@app.route('/api/cook/update_inventory', methods=['POST'])
def api_update_inventory():
    """Обновить склад"""
    user = get_current_user()
    if not user or user['role'] != 'cook':
        return jsonify({"error": "Доступ запрещён"}), 403

    data = request.get_json()
    product = data.get('product')
    change = data.get('change')
    unit = data.get('unit')

    if not product or change is None:
        return jsonify({"error": "Неверные данные"}), 400

    try:
        message = update_inventory(product, change, unit)
        return jsonify({"status": "ok", "message": message})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/cook/create_purchase_request', methods=['POST'])
def api_create_purchase_request():
    """Создать заявку на закупку"""
    user = get_current_user()
    if not user or user['role'] != 'cook':
        return jsonify({"error": "Доступ запрещён"}), 403

    data = request.get_json()
    product = data.get('product')
    quantity = data.get('quantity')
    unit = data.get('unit')

    if not product or not quantity or quantity <= 0:
        return jsonify({"error": "Неверные данные"}), 400

    try:
        message = create_purchase_request(user['username'], product, quantity, unit)
        return jsonify({"status": "ok", "message": message})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/cook/issued', methods=['GET'])
def api_view_issued():
    """Получить выданные блюда"""
    user = get_current_user()
    if not user or user['role'] != 'cook':
        return jsonify({"error": "Доступ запрещён"}), 403

    with sqlite3.connect('cafe.db') as conn:
        c = conn.cursor()
        c.execute('''
            SELECT u.username, m.name
            FROM meals ml
            JOIN users u ON ml.user_id = u.id
            JOIN menu m ON ml.menu_id = m.id
            WHERE ml.date = ?
            ORDER BY u.username, m.name
        ''', (current_date,))
        meals = c.fetchall()

    issued = [{"student": m[0], "dish": m[1]} for m in meals]
    return jsonify(issued)


@app.route('/api/cook/mark_delivered', methods=['POST'])
def api_mark_delivered():
    user = get_current_user()
    if not user or user['role'] != 'cook':
        return jsonify({"error": "Доступ запрещён"}), 403

    data = request.get_json()
    username = data.get('username')
    menu_id = data.get('menu_id')
    print(f"Получены данные: username={username}, menu_id={menu_id}")

    if not username or not menu_id:
        return jsonify({"error": "Неверные данные: укажите username и menu_id"}), 400

    try:
        mark_meal_delivered(username, int(menu_id))  # Приводим к int

        return jsonify({"status": "ok", "message": f"Блюдо выдано студенту {username}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# === Выход ===
@app.route('/logout')
def logout():
    try:
        session.pop('user_id', None)
    except Exception as e:
        print(str(e))
    return redirect(url_for('first_page'))




if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)


