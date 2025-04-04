import re
import asyncio
from datetime import datetime, timedelta

from telethon import TelegramClient

# Замените на свои данные из Telegram API
api_id = 'YOUR_API_ID'
api_hash = 'YOUR_API_HASH'
session_name = 'my_session'  # Имя файла сессии для постоянного подключения

# Регулярное выражение для поиска хештегов
hashtag_pattern = re.compile(r'#\w+')

client = TelegramClient(session_name, api_hash, api_id)

async def fetch_messages(entity, limit=1000):
    """
    Получает историю сообщений из указанного диалога (личные, группы, каналы, боты).
    """
    messages = await client.get_messages(entity, limit=limit)
    return messages

def extract_hashtag_messages(messages, target_hashtag=None):
    """
    Извлекает сообщения, содержащие хештеги.
    Если передан target_hashtag, возвращает только сообщения, где он присутствует.
    Возвращает список кортежей: (дата, текст, список найденных хештегов).
    """
    filtered = []
    for msg in messages:
        if msg.text:
            hashtags = hashtag_pattern.findall(msg.text)
            if target_hashtag:
                if target_hashtag in hashtags:
                    filtered.append((msg.date, msg.text, hashtags))
            else:
                if hashtags:
                    filtered.append((msg.date, msg.text, hashtags))
    return filtered

def get_report(messages):
    """
    Подсчитывает количество сообщений за последние 24 часа, неделю и месяц.
    """
    now = datetime.now(messages[0][0].tzinfo) if messages else datetime.now()
    one_day = now - timedelta(days=1)
    one_week = now - timedelta(weeks=1)
    one_month = now - timedelta(days=30)

    msgs_day = [m for m in messages if m[0] >= one_day]
    msgs_week = [m for m in messages if m[0] >= one_week]
    msgs_month = [m for m in messages if m[0] >= one_month]

    report = {
        'day': len(msgs_day),
        'week': len(msgs_week),
        'month': len(msgs_month)
    }
    return report

async def main():
    # Защита паролем
    password = input("Введите пароль: ")
    if password != "moloko123":
        print("Неверный пароль. Доступ запрещён.")
        return

    # Авторизация через сессию
    await client.start()
    
    # Вывод списка диалогов
    dialogs = await client.get_dialogs()
    print("Доступные диалоги:")
    for i, dialog in enumerate(dialogs, start=1):
        print(f"{i}. {dialog.name} (ID: {dialog.id})")
    
    # Пользователь выбирает нужный диалог (ID или username)
    entity = input("Введите ID или username диалога: ")
    messages = await fetch_messages(entity)
    
    # Ввод команды для поиска:
    # Команда "www" выводит все заявки (сообщения с любым хештегом),
    # а команда "w#<хештег>" выводит только сообщения с указанным хештегом.
    search_command = input("Введите команду поиска (www для всех заявок, или w#<ваш_хештег>, например: w#A910): ")
    if search_command.startswith("www"):
        # Все сообщения с хештегами
        hash_messages = extract_hashtag_messages(messages)
    elif search_command.startswith("w#"):
        tag = search_command[2:]
        if not tag.startswith("#"):
            tag = "#" + tag
        hash_messages = extract_hashtag_messages(messages, target_hashtag=tag)
    else:
        print("Неверная команда поиска.")
        await client.disconnect()
        return
    
    if hash_messages:
        report = get_report(hash_messages)
        print("\nОтчёт по выбранным сообщениям:")
        print("За день:", report['day'])
        print("За неделю:", report['week'])
        print("За месяц:", report['month'])
        print("\nСообщения:")
        for date, text, tags in hash_messages:
            print(f"{date.strftime('%Y-%m-%d %H:%M:%S')}: {text}")
    else:
        print("Сообщения не найдены.")

    await client.disconnect()

if __name__ == '__main__':
    asyncio.run(main())
