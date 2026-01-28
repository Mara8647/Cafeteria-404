import sqlite3
from flask import Flask, request, redirect, render_template, url_for
from datab import login


app = Flask(__name__, template_folder='./templates')

@app.route('/', methods=['POST', 'GET'])
def first_page():
    return render_template('first_page.html')


@app.route('/login', methods=['POST', 'GET'])
def login_page():
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')

        login.authorisation(username=username, password=password)

        return redirect(url_for('main_page',username=username))

    return render_template('login_page.html')


@app.route('/register', methods=['POST', 'GET'])
def register_page():
    if request.method == 'POST':
        role = request.form.get('selected_role', 'не указана')
        username = request.form.get('name', '')
        email = request.form.get('email', '')
        password = request.form.get('password', '')
        allergies = request.form.get('allergens', '')

        if allergies == '':
            allergies = 'none'

        if role == 'student':
            login.registration(username=username, email=email,
                              password=password, allergies=allergies, role=role)
        elif role == 'cook':
            login.registration(username=username, email=email,
                               password=password, role=role, allergies='none')

        elif role == 'admin':
            login.registration(username=username, email=email,
                               password=password, role=role, allergies='none')

        return redirect(url_for('main_page', username=username))

    return render_template('register_page.html')


@app.route('/main/<username>', methods=['POST', 'GET'])
def main_page(username):
    with sqlite3.connect('cafe.db') as connection:
        cursor = connection.cursor()
    role = str(cursor.execute("""SELECT role FROM users WHERE username = ?""", (username,)).fetchone())[2:-3]

    if role == 'student':
        return render_template('main_page_student.html', username=username)
    elif role == 'cook':
        return render_template('main_page_cook.html', username=username)
    elif role == 'admin':
        return render_template('main_page_admin.html', username=username)

if __name__ == '__main__':
    app.run(debug=True, port=5000)