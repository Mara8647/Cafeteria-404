# Школьная столовая (автоматизация)

## Docker


1. **Обязательно нужно создать в папке с dockerfile базу данных cafe.db!!!**

2. Создание образа:
    ```bash
    docker build -t cafeteria-404:latest .
    ```
3. Запуск контейнера при помощи compose.yml:
    ```compose.yml
    environment:
      APP_KEY: 'app_key' # Ключ для работы сервера
      ADMIN_PASSWORD: 'admin_passwd' # Пароль для администратора
      ADMIN_EMAIL: 'admin@gmail.com'
      COOK_PASSWORD: 'cook_passwd' # Пароль для повара
      COOK_EMAIL: 'cook@gmail.com'
    ```

4. После прописанной конфигурации вводим:
    ```bash
    docker compose up -d
    ```