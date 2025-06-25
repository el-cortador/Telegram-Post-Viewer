import os
import csv
from background import keep_alive
import pip
from telethon import TelegramClient, sync
from telethon.errors import FloodWaitError
import time

# Ввод API ID и API Hash
api_id = '20357601'
api_hash = '215e0e78e0a23d7c5e51dcf950a619a3'

# Создаем объект клиента
client = TelegramClient('session_name', api_id, api_hash)

# Входе в систему
client.start()

# Указываем канал, посты из которого спарсить
channel_username = 'channel_name'

# Открываем CSV-файл для записи
with open('messages.csv', 'w', newline='', encoding='utf-8') as csvfile:
    fieldnames = ['sender_id', 'text']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

    # Записываем заголовок
    writer.writeheader()

    # Получение сообщений и обработка ошибок
    try:
        # Получение последних n сообщений из канала
        messages = client.get_messages(channel_username, limit=200)

        # Выводим содержимое сообщений и записываем в CSV
        for message in messages:
            print(message.sender_id, message.text)
            writer.writerow({
                'sender_id': message.sender_id,
                'text': message.text
            })

    except FloodWaitError as e:
        print(f'Flood wait error: необходимо подождать {e.seconds} секунд.')
        time.sleep(e.seconds)
    except RpcError as e:
        print(f'Произошла ошибка RPC: {e}')

# Завершаем сессию клиента
client.disconnect()
