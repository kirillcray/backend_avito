# Django Pull Request Reviewer Service

Этот проект представляет собой микросервис для управления командами, пользователями и назначением ревьюеров на Pull Request'ы. Взаимодействие происходит полностью через HTTP API.

## Стек технологий

* **Python**
* **Django**
* **Django REST Framework**
* **PostgreSQL**
* **Docker**

## Структура моделей

### **Team (Команда)**

* `name` — название команды
* связь "один-ко-многим" с пользователями

### **User (Пользователь)**

* `user_id` — внешний ID
* `username` — имя пользователя
* `is_active` — активен или нет
* `team` — команда, которой принадлежит

### **PullRequest (Pull Request)**

* `pull_request_id`
* `pull_request_name`
* `author` (FK → User)
* `reviewers` (ManyToMany → User)
* `status`
* `created_at`, `merged_at`

## ⚙️ Установка и запуск

### 1. Клонировать репозиторий

```
 git clone https://github.com/kirillcray/backend_avito.git
 cd backend_avito
```

### 2. Переименовать `.env.example` в `.env`

### 3. Запустить проект

```
docker compose up --build
```

При запуске автоматически применяются миграции:

* `python manage.py migrate`


## Админка

Админ-панель доступна по адресу:

```
/admin/
```

В ней можно управлять:

* пользователями
* командами
* Pull Request'ами

---

## API Endpoints

* `POST /team/add Создать команду с участниками`
* `GET /team/get Получить команду с участниками`

* `POST /users/setIsActive Установить флаг активности пользователя`
* `GET /users/getReview Получить PR, где пользователь является ревьюером`

* `POST /pullRequest/create Создать Pull Request с назначением ревьюеров`
* `POST /pullRequest/merge Отметить Pull Request как смёрженный`
* `POST /pullRequest/reassign Переназначить ревьюеров на Pull Request`


