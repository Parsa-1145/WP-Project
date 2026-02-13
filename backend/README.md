# WP-Project Backend

This is the backend for the WP-Project web application, developed using Django. It provides APIs and handles data management for the frontend application.

# Quick Start (Developmet)

To get started with the project, follow these steps:
1. **Install the package manager(PDM)**
    ```bash
    pip install pdm
    ```
2. **Install dependencies**
    ```bash
    pdm install --dev
    ```
3. **Environment Variables**
    ```bash
    cp .env.example .env
    ```
    Update the `.env` file with your configuration. Fill the *DJANGO_SECRET_KEY* and *DATABASE_URL*
4. **Run Migrations**
    ```bash
    pdm run python manage.py migrate
    pdm run python manage.py makemigrations
    ```
5. **Start the Development Server**
    ```bash
    pdm run python manage.py runserver
    ```
