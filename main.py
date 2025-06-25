import telebot
from secrets import secrets
from telebot import types

# Передаем токен бота
token = secrets.get('BOT_API_TOKEN')
bot = telebot.TeleBot(token)


# Хендлер и функция для обработки команды /start
@bot.message_handler(commands=['start'])
def start_message(message):
  # создаём кнопки бота
  markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
  start_button = types.KeyboardButton("Старт")
  action_button = types.KeyboardButton("Комплимент")
  markup.add(start_button, action_button)
  # Приветсвенное сообщение для команды /start
  bot.send_message(
      message.chat.id,
      text="Привет, {0.first_name} \nВоспользуйся кнопками".format(
          message.from_user),
      reply_markup=markup)


# Хендлер для обработки нажатий кнопок
@bot.message_handler(content_types=['text'])
def buttons(message):
  if (message.text == "Старт"):
    bot.send_message(
        message.chat.id,
        text=
        "Я могу поддержать тебя и поднять настроение. Просто попроси об этом")
  elif (message.text == "Начать парсинг"):
    bot.send_message(message.chat.id, text=f"{random.choice(compliments)}")
  else:
    bot.send_message(message.chat.id,
                     text="Я могу отвечать только на нажатие кнопок")


# Бесконечное выполнение кода
bot.polling(none_stop=True, interval=0)
