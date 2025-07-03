from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
import os
import asyncio
import sqlite3

API_TOKEN = os.getenv("TELEGRAM_TOKEN")

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
# Таблица заданий
cursor.execute('''
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id INTEGER,
    decription TEXT,
    reward INTEGER
)
''')
conn.commit()

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
        "/users - показать список юзеров\n"
        "/balance - проверить баланс\n"
        "/give - начислить виштокены за хорошее поведение или выполнение задания\n"
        "/settask - добавить задание\n"
        "/tasks - посмотреть список заданий\n"
        "/amendtask - заменить задание\n"
        "/deletetask - удалить задание\n"
        "/taskdone - отправить запрос о выполнении задания\n"
        "(скоро появятся другие команды)"
    )

@dp.message(Command("users"))
async def cmd_users(message: types.Message):
    cursor.execute(
        "SELECT username, balance FROM users"
    )
    rows = cursor.fetchall()
    if not rows:
        await message.answer("Пользователи пока не зарегистрированы.")
        return
    text = "Список участников:\n"
    for username, balance in rows:
        display_name = f"@{username}" if username else "(без имени)"
        text += f"{display_name} — {balance} виштокенов\n"
    await message.answer(text)

@dp.message(Command("balance"))
async def cmd_balance(message: types.Message):
    cursor.execute(
        'SELECT balance FROM users WHERE user_id = ?',
        (message.from_user.id,)
    )
    row = cursor.fetchone()
    balance = row[0] if row else 0
    await message.answer(f"Твой баланс: {balance} виштокенов")

@dp.message(Command("give"))
async def cmd_give(message: types.Message):
    parts = message.text.strip().split()
    if len(parts) < 3:
        await message.answer("Формат команды: /give @username количество")
        return
    to_username = parts[1].lstrip("@")
    try:
        amount = int(parts[2])
    except ValueError:
        await message.answer("Нужно указать число виштокенов. :)")
        return
    if amount <=0:
        await message.answer("Количество должно быть больше ноля.")
        return
    cursor.execute(
        "SELECT user_id FROM users WHERE username = ?",
        (to_username,)
    )
    row = cursor.fetchone()
    if not row:
        await message.answer("Такой пользователь не найден. :(")
        return
    to_user_id = row[0]
    if to_user_id == message.from_user.id:
        await message.answer("Хитро, но себе начислять нельзя. :)")
        return
    cursor.execute(
        "UPDATE users SET balance = balance + ? WHERE user_id = ?",
        (amount, to_user_id)
    )
    conn.commit()
    await message.answer(
        f"Вы успешно отправили {amount} виштокенов @{to_username}!"
    )
    await bot.send_message(
        to_user_id,
        f"Вам начислили {amount} виштокенов от @{message.from_user.username} ! :)"
    )

@dp.message(Command("settask"))
async def cmd_settask(message: types.Message):
    text = message.text.strip().replace("\n", " ")
    if "/" not in text:
        await message.answer("Формат команды: /settask описание задания /вознаграждение")
    return
    try:
        parts = text.split("/", 1)
        description = parts[0].replace("/settask", "").strip()
        reward = int(parts[1].strip())
    except Exception:
        await message.answer("Убедись, что всё написано правильно. ^^,")
        return
    if not description:
        await message.answer("Описание задания не может быть пустым. :]")
        return
    if reward <= 0:
        await message.answer("А почему нагрды нет никакой? :(")
        return
    # Сохраняем задание и увдемоляем пользователей
    cursor.execute(
        "INSERT INTO tasks (owner_id, description, reward) VALUES (?, ?, ?)",
        (message.from_user.id, description, reward)
    )
    conn.commit()
    await message.answer(
        f"Задание создано:\n\n\"{description}\"\nВознаграждение: {reward} токенов."
    )
    cursor.execute(
        "SELECT user_id FROM users WHERE user_id != ?",
        (message.from_user.id,)
    )   
    other_users = cursor.fetchall()
    for (user_id) in other_users:
        await bot.send_message(
            user_id,
            f"@{message.from_user.username} создал новое задание. :)"
        )        

# Запуск
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
