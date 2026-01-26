import sqlite3
from datetime import date


# Переводит формат дат python в понятный для sqlite формат
def adapt_date(val: date) -> str:
    return val.isoformat()

sqlite3.register_adapter(date, adapt_date)

current_date = date.today()


# um = input("Введите имя пользователя: ")
# pw = input("Введите пароль: ")
# email = input("Введите почту: ")
# npt = input("Введите новый способ оплаты: ")
# role = input("Введите роль: ")
# alrg = input("Введите аллергии: ")


# Функция отвечающая за регистрацию
def registration(username, email, password, payment_type, role, allergies):
    # Ограничиваем возможность регистрации администратора
    final_role = 'user' if role.lower() == 'admin' else role
    with sqlite3.connect('cafe.db') as connection:
        cursor = connection.cursor()
        # Выполняется запрос на регистрацию
        try:
            # Регистрируем пользователя с is_approved = FALSE
            cursor.execute("""
                    INSERT INTO users (username, email, password, payment_type, user_balance, role, allergies, is_approved) 
                    VALUES (?, ?, ?, ?, 0.0, ?, ?, FALSE)
                """, (username, email, password, payment_type, final_role, allergies))
            print(f"{username}, твоя заявка на регистрацию отправлена. Жди подтверждения администратором.")
        except sqlite3.IntegrityError:  # Если пользователь уже существует выводим "ошибку" !!!Только для случая когда IntegrityError!!!
            print("Такое имя пользователя или email уже занято.")


# Функция отвечающая за авторизацию юзера
def authorisation(username, password):
    with sqlite3.connect('cafe.db') as connection:
        cursor = connection.cursor()
        # Выполняется запрос на авторизацию
        # Добавляем проверку is_approved
        cursor.execute("SELECT id, role FROM users WHERE username = ? AND password = ? AND is_approved = TRUE",
                        (username, password))
        user = cursor.fetchone()
        # Если юзер есть и его аккаунт подтвержден, приветствуем, иначе отказ
        if user is not None:
            print(f'Привет, {username}!')
            return user
        else:
            # Проверяем, существует ли пользователь, но не подтвержден
            cursor.execute("SELECT id, role FROM users WHERE username = ? AND password = ? AND is_approved = FALSE",
                            (username, password))
            unconfirmed_user = cursor.fetchone()
            if unconfirmed_user:
                print(f'{username}, твоя регистрация еще не подтверждена администратором.')
            else:
                print(f'Во входе отказано. Проверь имя и пароль.')
            return None
    # P.S. возвращаем user для последующей проверки выдачи питания и проверки роли пользователя (по id и role)


# Функция отвечающая за изменение способа оплаты
# Принимает user_id явно, а не вызывает authorisation внутри себя
def change_payment_type(user_id, new_payment_type):
    with sqlite3.connect('cafe.db') as connection:
        cursor = connection.cursor()
        cursor.execute("UPDATE users SET payment_type = ? WHERE id = ?", (new_payment_type, user_id))


# Функция для администратора: просмотр неподтвержденных регистраций
def admin_view_pending_registrations(admin_user_data):
    if not admin_user_data or admin_user_data[1] != 'admin':
        print("Ошибка: Только администратор может просматривать заявки.")
        return []

    with sqlite3.connect('cafe.db') as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT id, username, email, role FROM users WHERE is_approved = FALSE")
        pending_users = cursor.fetchall()

        if not pending_users:
            print("Нет неподтвержденных регистраций.")
        else:
            print("\n--- Список неподтвержденных регистраций ---")
            for user in pending_users:
                print(f"ID: {user[0]}, Имя: {user[1]}, Email: {user[2]}, Роль: {user[3]}")
        return pending_users


# Функция для администратора: одобрение или отклонение заявки
def admin_approve_or_deny_user(admin_user_data, user_id_to_process, action):
    """
    Администратор подтверждает или отклоняет регистрацию пользователя.
    admin_user_data - результат вызова authorisation для администратора (id, role).
    user_id_to_process - ID пользователя, чью заявку нужно обработать.
    action - строка 'approve' или 'deny'.
    """
    if not admin_user_data or admin_user_data[1] != 'admin':
        print("Ошибка: Только администратор может подтверждать или отклонять регистрации.")
        return False

    if action not in ['approve', 'deny']:
        print("Ошибка: Действие должно быть 'approve' или 'deny'.")
        return False

    with sqlite3.connect('cafe.db') as connection:
        cursor = connection.cursor()
        try:
            # Проверяем, существует ли пользователь с таким ID и не подтвержден ли он
            cursor.execute("SELECT id, username, is_approved FROM users WHERE id = ? AND is_approved = FALSE",
                            (user_id_to_process,))
            user = cursor.fetchone()

            if user:
                username = user[1]
                if action == 'approve':
                    # Подтверждаем регистрацию
                    cursor.execute("UPDATE users SET is_approved = TRUE WHERE id = ?", (user_id_to_process,))
                    print(f"Регистрация пользователя '{username}' успешно подтверждена администратором.")
                elif action == 'deny':
                    # Удаляем пользователя из базы данных
                    cursor.execute("DELETE FROM users WHERE id = ?", (user_id_to_process,))
                    print(f"Заявка пользователя '{username}' отклонена и удалена из системы администратором.")
                return True
            else:
                print(f"Пользователь с ID '{user_id_to_process}' не найден или уже обработан.")
                return False
        except sqlite3.Error as e:
            print(f"Произошла ошибка при обработке заявки: {e}")
            return False
        

admin_approve_or_deny_user([0, 'admin'], 2, 'approve')