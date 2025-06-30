from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
import asyncio
import sqlite3

API_TOKEN = ''

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Создаем или подключаем базу данных
conn = sqlite3.connect('wishtracker.db')
cursor = conn.cursor()

# Таблица пользователей
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    balance INTEGER DEFAULT 0
)
''')
conn.commit()

# /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    # Добавляем пользователя, если его нет
    cursor.execute(
        'INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)',
        (message.from_user.id, message.from_user.username or "")
    )
    conn.commit()
    await message.answer(
        "Привет! Я трекер желаний. :)\n\n"
        "Регистрация успешна.\n"
        "Команды:\n"
        "/balance - проверить баланс\n"
        "(скоро появятся другие команды)"
    )

# /balance
@dp.message(Command("balance"))
async def cmd_balance(message: types.Message):
    cursor.execute(
        'SELECT balance FROM users WHERE user_id = ?',
        (message.from_user.id,)
    )
    row = cursor.fetchone()
    balance = row[0] if row else 0
    await message.answer(f"Твой баланс: {balance} виштокенов")

# Запуск
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
