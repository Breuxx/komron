from fastapi import FastAPI, HTTPException, Query
import uvicorn
import re
import asyncio
from datetime import datetime, timedelta
from telethon import TelegramClient

# Создаем ASGI-приложение
app = FastAPI()

# Конфигурация для Telegram API
api_id = '1403467'  # Ваш API ID
api_hash = '15525849e4b493d2143b175f96825f87'  # Ваш API hash
session_name = 'my_session'  # Имя файла сессии

# Регулярное выражение для поиска хештегов
hashtag_pattern = re.compile(r'#\w+')

# Создаем клиента Telethon
client = TelegramClient(session_name, api_id, api_hash)

@app.on_event("startup")
async def startup_event():
    await client.start()

@app.get("/dialogs")
async def get_dialogs(password: str = Query(..., description="Пароль для доступа")):
    """
    Возвращает список диалогов (личные, группы, каналы и т.д.).
    Для доступа необходимо передать параметр password=moloko123.
    """
    if password != "moloko123":
        raise HTTPException(status_code=403, detail="Неверный пароль")
    dialogs = await client.get_dialogs()
    return [{"name": d.name, "id": d.id} for d in dialogs]

def extract_hashtag_messages(messages, target_hashtag=None):
    """
    Извлекает сообщения, содержащие хештеги.
    Если указан target_hashtag, возвращает только те сообщения, где он присутствует.
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
    return {"day": len(msgs_day), "week": len(msgs_week), "month": len(msgs_month)}

@app.get("/report")
async def report(
    entity: str = Query(..., description="ID или username диалога"),
    search_command: str = Query(..., description="Команда поиска: www для всех заявок или w#<хештег> для фильтрации"),
    password: str = Query(..., description="Пароль для доступа")
):
    """
    Возвращает отчёт по сообщениям выбранного диалога.
    - entity: ID или username диалога (например, 'username' или '-123456789')
    - search_command: 'www' – для выборки всех сообщений с хештегами, или 'w#A910' – для поиска по конкретному хештегу.
    - password: Пароль доступа (moloko123)
    """
    if password != "moloko123":
        raise HTTPException(status_code=403, detail="Неверный пароль")
    
    messages = await client.get_messages(entity, limit=1000)
    
    if search_command.startswith("www"):
        hash_messages = extract_hashtag_messages(messages)
    elif search_command.startswith("w#"):
        tag = search_command[2:]
        if not tag.startswith("#"):
            tag = "#" + tag
        hash_messages = extract_hashtag_messages(messages, target_hashtag=tag)
    else:
        raise HTTPException(status_code=400, detail="Неверная команда поиска")
    
    report_data = get_report(hash_messages) if hash_messages else {}
    messages_list = [
        {"date": m[0].strftime("%Y-%m-%d %H:%M:%S"), "text": m[1], "hashtags": m[2]}
        for m in hash_messages
    ]
    return {"report": report_data, "messages": messages_list}

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000)