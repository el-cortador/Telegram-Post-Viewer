import telebot
import os
import csv
import tempfile
import pip
import pyOpenSSL

pip.main(['install', 'pytelegrambotapi'])
import time
import asyncio
from secrets import secrets
from telebot import types
from telethon import TelegramClient
from telethon.errors import FloodWaitError
from threading import Thread
from background import keep_alive

# Передаем токен бота
token = secrets.get('BOT_API_TOKEN')
bot = telebot.TeleBot(token)

# API данные для Telethon
api_id = 'API_ID'
api_hash = 'API_HASH'

# Словарь для хранения состояния пользователей
user_states = {}


# Состояния бота
class States:
  WAITING_CHANNEL = "waiting_channel"
  WAITING_COUNT = "waiting_count"


# Хендлер для команды /start
@bot.message_handler(commands=['start'])
def start_message(message):
  markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
  start_button = types.KeyboardButton("Начать парсинг")
  markup.add(start_button)

  bot.send_message(
      message.chat.id,
      text=
      "Привет, {0.first_name}!\nЯ бот для парсинга постов из Telegram каналов.\nНажми 'Начать парсинг' для начала работы."
      .format(message.from_user),
      reply_markup=markup)


# Хендлер для обработки текстовых сообщений
@bot.message_handler(content_types=['text'])
def handle_text(message):
  user_id = message.from_user.id

  if message.text == "Начать парсинг":
    # Убираем клавиатуру и просим ввести название канала
    markup = types.ReplyKeyboardRemove()
    bot.send_message(
        message.chat.id,
        text=
        "Введите название канала (например: @channel_name или channel_name):",
        reply_markup=markup)
    user_states[user_id] = States.WAITING_CHANNEL

  elif user_id in user_states and user_states[
      user_id] == States.WAITING_CHANNEL:
    # Сохраняем название канала и просим количество постов
    if not hasattr(message, 'channel_name'):
      user_states[user_id] = {
          'state': States.WAITING_COUNT,
          'channel': message.text
      }

    # Создаем кнопки с вариантами количества постов
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    btn_10 = types.KeyboardButton("10")
    btn_20 = types.KeyboardButton("20")
    btn_50 = types.KeyboardButton("20")
    btn_100 = types.KeyboardButton("100")
    btn_150 = types.KeyboardButton("150")
    btn_200 = types.KeyboardButton("200")
    markup.add(btn_10, btn_20, btn_100)

    bot.send_message(message.chat.id,
                     text="Выберите количество постов для парсинга:",
                     reply_markup=markup)

  elif user_id in user_states and isinstance(
      user_states[user_id],
      dict) and user_states[user_id]['state'] == States.WAITING_COUNT:
    # Проверяем, что введено корректное количество
    try:
      count = int(message.text)
      if count not in [10, 20, 50, 100, 150, 200]:
        bot.send_message(
            message.chat.id,
            "Пожалуйста, выберите одно из предложенных значений: 10, 20 или 100"
        )
        return

      channel_name = user_states[user_id]['channel']

      # Убираем клавиатуру и начинаем парсинг
      markup = types.ReplyKeyboardRemove()
      bot.send_message(
          message.chat.id,
          text="Начинаю парсинг канала {} ({} постов)...\nПожалуйста, подождите."
          .format(channel_name, count),
          reply_markup=markup)

      # Запускаем парсинг в отдельном потоке
      thread = Thread(target=parse_channel,
                      args=(message.chat.id, channel_name, count))
      thread.start()

      # Очищаем состояние пользователя
      del user_states[user_id]

    except ValueError:
      bot.send_message(
          message.chat.id,
          "Пожалуйста, выберите одно из предложенных значений: 10, 20 или 100")

  else:
    # Если пользователь пишет что-то неожиданное
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    start_button = types.KeyboardButton("Начать парсинг")
    markup.add(start_button)

    bot.send_message(message.chat.id,
                     text="Для начала работы нажмите 'Начать парсинг'",
                     reply_markup=markup)


def parse_channel(chat_id, channel_name, count):
  """Функция парсинга канала"""
  try:
    # Создаем клиента Telethon
    client = TelegramClient('session_name', api_id, api_hash)

    async def do_parsing():
      await client.start()

      try:
        # Получаем сообщения из канала
        messages = await client.get_messages(channel_name, limit=count)

        # Создаем временный файл для CSV
        with tempfile.NamedTemporaryFile(mode='w',
                                         suffix='.csv',
                                         delete=False,
                                         encoding='utf-8',
                                         newline='') as csvfile:
          fieldnames = ['message_id', 'date', 'sender_id', 'text', 'views']
          writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

          # Записываем заголовок
          writer.writeheader()

          # Записываем сообщения
          for message in messages:
            writer.writerow({
                'message_id':
                message.id,
                'date':
                message.date.strftime('%Y-%m-%d %H:%M:%S')
                if message.date else '',
                'sender_id':
                message.sender_id,
                'text':
                message.text if message.text else '',
                'views':
                message.views if message.views else 0
            })

          temp_file_path = csvfile.name

        await client.disconnect()

        # Отправляем файл пользователю
        with open(temp_file_path, 'rb') as file:
          bot.send_document(
              chat_id,
              file,
              caption=
              f"Парсинг завершен!\nКанал: {channel_name}\nКоличество постов: {len(messages)}"
          )

        # Удаляем временный файл
        os.unlink(temp_file_path)

        # Предлагаем начать новый парсинг
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        start_button = types.KeyboardButton("Начать парсинг")
        markup.add(start_button)

        bot.send_message(chat_id,
                         text="Готов к новому парсингу!",
                         reply_markup=markup)

      except FloodWaitError as e:
        bot.send_message(
            chat_id,
            f"Ошибка: превышен лимит запросов. Необходимо подождать {e.seconds} секунд."
        )
      except Exception as e:
        bot.send_message(chat_id, f"Произошла ошибка при парсинге: {e}")

    # Запускаем асинхронную функцию парсинга
    asyncio.run(do_parsing())

  except Exception as e:
    bot.send_message(chat_id, f"Произошла ошибка: {e}")


if __name__ == '__main__':
  # Запускаем keep_alive для поддержания работы
  keep_alive()

  # Запускаем бота
  print("Бот запущен...")
  bot.polling(none_stop=True, interval=0)
