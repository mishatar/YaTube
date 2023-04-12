# Социальная сеть Yatube

### Краткое описание

Yatube это платформа для создания блогов, поиска друзей и обмена мнениями.

### Технологии 
Python 3.7 
Django 2.2.19 

### Функционал проекта: 
- регистрация пользователей с возможностью восстановления пароля
- подписка на авторов
- добавление комментариев
- поиск
- кеширование
- пагинация

### Запуск проекта в dev-режиме 
- Установите и активируйте виртуальное окружение
    ``` python -m venv env ```
- Установите зависимости из файла requirements.txt 
- ``` pip install -r requirements.txt ``` 
- Выполнить миграции:
- ``` python manage.py migrate```
- В папке с файлом manage.py выполните команду: 
- ``` python manage.py runserver ``` 

