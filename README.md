# Мастер дедлайнов — Telegram-бот для задач с датами

**Мастер дедлайнов** помогает небольшим командам ставить задачи с дедлайнами, смотреть их в личке и получать ежедневные напоминания.

- Создание задач из группы:  
  `/task <описание> до <дата> @username`
- Личные команды: `/my`, `/today`, `/week`, `/overdue`
- Закрытие задач: `/done <id>`
- Ежедневный дайджест в 09:00 (настраивается)

---

## 1. Требования

- **Python** 3.11+
- **PostgreSQL** 13+ (подойдёт и новее)
- Аккаунт Telegram‑бота (через @BotFather) и его `BOT_TOKEN`

---

## 2. Технологический стек

- **aiogram 3.x** — Telegram API (async)
- **SQLAlchemy 2.x (async)** + **asyncpg** — доступ к PostgreSQL
- **python-dotenv** — конфиги из `.env`
- **APScheduler** — планировщик ежедневных дайджестов
- **logging** — стандартный логгер Python

---

## 3. Установка и запуск локально (Linux/macOS/WSL)

```bash
# 1) Клонируем репозиторий
git clone <URL вашего репозитория> deadline_bot
cd deadline_bot

# 2) Создаём и активируем виртуальное окружение
python3.11 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3) Устанавливаем зависимости
pip install -r requirements.txt

# 4) Создаём БД (пример — локальный Postgres)
# Предполагается, что PostgreSQL установлен и запущен
# Создайте пользователя/БД (примерные команды):
#   sudo -u postgres createuser -P deadline_user     # задайте пароль
#   sudo -u postgres createdb -O deadline_user deadline_db

# 5) Создаём .env из примера и заполняем
cp .env.example .env
# отредактируйте .env: BOT_TOKEN, DATABASE_URL и др.

# 6) Создаём таблицы
python scripts/create_db_tables.py

# 7) Запускаем бота (polling)
python -m app.main
