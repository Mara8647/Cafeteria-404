import sqlite3
from flask import Flask, request, redirect, render_template, url_for, jsonify, session
from datab import login, dbInitialisation, payment, student

app = Flask(__name__, template_folder='./templates')
app.secret_key = 'cafe_secret_key_2026'  # нужно создать нормальный ключ



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


        with sqlite3.connect('cafe.db') as conn:
            cursor = conn.cursor()

            cursor.execute("INSERT INTO users (username, email, password, payment_type, user_balance, role, allergies) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                            (username, email, password, 'single', 0.0, role, allergies))

            user_id = cursor.lastrowid

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
        balance = str(cursor.execute("""SELECT user_balance FROM users WHERE id = ?""", (user['id'],)).fetchone())
        balance = balance[1:len(balance)-2]
        print(balance)

    if user['role'] == 'student':
        return render_template('main_page_student.html', username=user['username'], balance=balance)
    elif user['role'] == 'cook':
        return render_template('main_page_cook.html', username=user['username'])
    elif user['role'] == 'admin':
        return render_template('main_page_admin.html', username=user['username'])
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
    return jsonify(menu_items or [])


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

    # Сохраняем заказ и оплату
    status = payment.pay(user['username'], items, payment_type)
    student.receive_meal(user['username'], items)
    print(status)

    return jsonify({
        "status": status,
        "total": total
    })


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

    if not meal_name or not isinstance(rating, int) or not (1 <= rating <= 5):
        return jsonify({"error": "Неверные данные"}), 400

    success = student.leave_review(
        username=user['username'],
        meal_name=meal_name,
        rating=rating,
        comment=comment
    )

    if success:
        return jsonify({"status": "ok"})
    else:
        return jsonify({"error": "Не удалось сохранить отзыв"}), 500


@app.route('/api/reviews', methods=['GET'])
def get_reviews():
    dish_name = request.args.get('dish')
    if not dish_name:
        return jsonify([])

    with sqlite3.connect('cafe.db', timeout=20.0) as conn:
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


# === Выход ===
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('first_page'))




if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)



