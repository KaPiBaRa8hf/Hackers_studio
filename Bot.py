from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
import sqlite3
import random
import os

# Підключення БД
conn = sqlite3.connect('countries.db')
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS countries
                  (user_id INTEGER PRIMARY KEY, 
                   name TEXT,
                   username TEXT,  # <- Новий стовпець
                   gold INTEGER DEFAULT 100,
                   army INTEGER DEFAULT 10,
                   oil INTEGER DEFAULT 50)''')

class CountryGame:
    @staticmethod
    def create_country(user_id, name):
        cursor.execute("INSERT OR IGNORE INTO countries VALUES (?, ?, 100, 10, 50)", (user_id, name))
        conn.commit()

    @staticmethod
    def attack(attacker_id, defender_id):
        cursor.execute("SELECT army FROM countries WHERE user_id=?", (attacker_id,))
        attacker_army = cursor.fetchone()[0]
        
        cursor.execute("SELECT army FROM countries WHERE user_id=?", (defender_id,))
        defender_army = cursor.fetchone()[0]
        
        if attacker_army > defender_army:
            loot = random.randint(10, 50)
            cursor.execute("UPDATE countries SET gold=gold+? WHERE user_id=?", (loot, attacker_id))
            cursor.execute("UPDATE countries SET army=army-? WHERE user_id=?", (defender_army//2, defender_id))
            conn.commit()
            return f"Перемога! Ви отримали {loot} золота."
        else:
            return "Поразка! Ваша армія замала."

def start(update: Update, context: CallbackContext):
    user = update.effective_user
    username = user.username or ""  # Якщо username не вказано, зберігаємо пусту строку
    cursor.execute(
        "INSERT OR IGNORE INTO countries VALUES (?, ?, ?, 100, 10, 50)",
        (user.id, user.first_name, username)
    )
    conn.commit()
    update.message.reply_text(f"🏰 Країна {user.first_name} створена!")

def attack(update: Update, context: CallbackContext):
    if not context.args:
        update.message.reply_text("Вкажіть гравця: /attack @username")
        return

    attacker_id = update.effective_user.id
    defender_username = context.args[0].strip('@')

    # Отримуємо дані атакуючого
    cursor.execute("SELECT army, gold FROM countries WHERE user_id=?", (attacker_id,))
    attacker = cursor.fetchone()
    if not attacker:
        update.message.reply_text("Ви не зареєстровані! Використовуйте /start")
        return

    attacker_army, attacker_gold = attacker

    # Отримуємо дані захисника
    cursor.execute("SELECT user_id, army, gold FROM countries WHERE username=?", (defender_username,))
    defender = cursor.fetchone()
    if not defender:
        update.message.reply_text("Гравець не знайдений!")
        return

    defender_id, defender_army, defender_gold = defender

    # Уникаємо атаки самого себе
    if attacker_id == defender_id:
        update.message.reply_text("Не можна атакувати себе!")
        return

    # Розрахунок битви (з випадковим елементом)
    attacker_power = attacker_army * random.uniform(0.8, 1.2)
    defender_power = defender_army * random.uniform(0.8, 1.2)

    if attacker_power > defender_power:
        # Атакуючий перемагає
        loot_percentage = random.randint(10, 30)  # % золота, яке забере переможець
        loot = int(defender_gold * loot_percentage / 100)
        army_loss = random.randint(30, 70)  # % втрат армії

        # Оновлюємо дані
        cursor.execute("""
            UPDATE countries 
            SET gold = gold + ?, 
                army = army - ROUND(army * ? / 100) 
            WHERE user_id = ?
        """, (loot, army_loss, attacker_id))

        cursor.execute("""
            UPDATE countries 
            SET gold = gold - ?, 
                army = ROUND(army * ? / 100) 
            WHERE user_id = ?
        """, (loot, 100 - army_loss, defender_id))

        conn.commit()
        
        update.message.reply_text(
            f"🎯 Ви перемогли {defender_username}!\n"
            f"💰 Виграш: {loot} золота\n"
            f"⚔️ Втрати армії: {army_loss}%"
        )
    else:
        # Атакуючий програє
        army_loss = random.randint(40, 80)
        cursor.execute("""
            UPDATE countries 
            SET army = ROUND(army * ? / 100) 
            WHERE user_id = ?
        """, (100 - army_loss, attacker_id))
        conn.commit()
        
        update.message.reply_text(
            f"💥 Ви програли битву з {defender_username}!\n"
            f"⚔️ Втрати армії: {army_loss}%"
        )

def main():
    TOKEN = os.getenv("BOT_TOKEN")  # Отримуємо токен із змінних середовища
    updater = Updater(TOKEN)
    updater.dispatcher.add_handler(CommandHandler("start", start))
    updater.dispatcher.add_handler(CommandHandler("attack", attack))
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()