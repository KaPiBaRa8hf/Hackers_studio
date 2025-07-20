from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, CallbackQueryHandler
import sqlite3
import random

# Налаштування БД
conn = sqlite3.connect('countries.db')
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS countries
                  (user_id INTEGER PRIMARY KEY, 
                   name TEXT, 
                   gold INTEGER DEFAULT 100,
                   army INTEGER DEFAULT 10,
                   oil INTEGER DEFAULT 50)''')

# Клас гри
class CountryGame:
    @staticmethod
    def create_country(user_id, name):
        cursor.execute("INSERT INTO countries VALUES (?, ?, 100, 10, 50)", (user_id, name))
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

# Обробники команд
def start(update: Update, context: CallbackContext):
    user = update.effective_user
    CountryGame.create_country(user.id, user.first_name)
    update.message.reply_text(
        f"🏰 Країна {user.first_name} створена!\n"
        f"🪙 Золото: 100\n"
        f"⚔️ Армія: 10\n"
        f"⛽ Нафта: 50"
    )

def attack(update: Update, context: CallbackContext):
    defender = context.args[0].strip('@')
    # Тут має бути логіка пошуку ID гравця за ніком
    result = CountryGame.attack(update.effective_user.id, defender)
    update.message.reply_text(result)

# Запуск бота
updater = Updater("8156143984:AAFdyGAeVd9EK8BS9lidMFl_JGM8x2Unh7E")
updater.dispatcher.add_handler(CommandHandler("start", start))
updater.dispatcher.add_handler(CommandHandler("attack", attack))
updater.start_polling()