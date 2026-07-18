import os
import json
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel
import telebot
import requests
import threading
import uvicorn

load_dotenv()

app = FastAPI()

DB_FILE = 'db.json'

PROMPT_ABSURD = "Ты — генератор невероятно абсурдных, фантастических и очень смешных оправданий. Твой ответ должен состоять строго из одной фразы. Отмазка должна звучать дико и уморительно (например: похищение инопланетянами, битва с драконом по пути, застревание в текстурах реальности, восстание домашних тапочек). Никакой банальщины и скучной вежливости. Сразу выдавай готовую отмазку без приветствий, списков, извинений и советов."
PROMPT_PLAUSIBLE = "Ты — генератор очень правдоподобных, вежливых и уважительных оправданий для учебы. Твой ответ должен состоять строго из одной фразы. Отмазка должна звучать максимально естественно, повседневно и вызывать доверие (например: непредвиденная задержка общественного транспорта, мелкий бытовой форс-мажор с коммунальными службами, легкое внезапное недомогание). Избегай глупых, подозрительных или слишком сложных историй. Обязательно начни фразу с искреннего и вежливого извинения. Сразу выдавай готовую отмазку без приветствий, списков и советов."

CURRENT_PROMPT = PROMPT_PLAUSIBLE

class GenerateRequest(BaseModel):
    situation: str
    mode: str

def read_db():
    if not os.path.exists(DB_FILE):
        return []
    with open(DB_FILE, 'r', encoding='utf-8') as file:
        try:
            return json.load(file)
        except:
            return []

def write_db(data):
    with open(DB_FILE, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

@app.get("/")
def home_page():
    return FileResponse("templates/index.html")

@app.get("/generate")
def generate_page():
    return FileResponse("templates/generate.html")

@app.get("/api/excuses")
def get_excuses():
    data = read_db()
    return data[::-1][:5]

@app.post("/api/generate-excuse")
def api_generate_excuse(req: GenerateRequest):
    system_prompt = PROMPT_ABSURD if req.mode == "absurd" else PROMPT_PLAUSIBLE
    ai_result = ask_groq(req.situation, system_prompt)
    
    db_data = read_db()
    db_data.append({"situation": req.situation, "excuse": ai_result})
    write_db(db_data)
    
    return {"excuse": ai_result}

def ask_groq(prompt_text, system_prompt):
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    API_URL = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt_text}
        ],
        "temperature": 0.8 if system_prompt == PROMPT_ABSURD else 0.6
    }
    response = requests.post(API_URL, headers=headers, json=payload)
    if response.status_code == 200:
        return response.json()['choices'][0]['message']['content']
    return "Мой кот съел кабель интернета, поэтому я не смог сгенерировать отмазку."

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    responce_text = (
        "🤖 ДОБРО ПОЖАЛОВАТЬ В ОТМАЗКОГЕНЕРАТОР 3000! 🤖\n\n"
        "Привет! Я твой личный ИИ-помощник, созданный спасать тебя из самых неловких ситуаций в учебе и жизни! 🎓⚡\n\n"
        "Накосячил? Опоздал? Забыл домашку? Не паникуй! Я сгенерирую для тебя оправдание, в которое поверит даже самый строгий препод! 🤥👌\n\n"
    )
    bot.send_message(message.chat.id, responce_text)

@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = "Доступные команды:\n /start - Запуск бота \n /help - Выводит список возможных команд \n /generate - Генерирует отмазку по заданному промпту \n /prompts - Выводит список готовых промптов\n /prompt - Задает промпт"
    bot.send_message(message.chat.id, help_text)

@bot.message_handler(commands=['prompts'])
def send_prompts(message):
    prompts = (
        "📋 ДОСТУПНЫЕ РЕЖИМЫ ГЕНЕРАЦИИ\n\n"
        "Скопируйте нужный текст команды целиком и отправьте боту:\n\n"
        "🤪 1. АБСУРДНЫЕ И СМЕШНЫЕ ОТМАЗКИ\n"
        "/prompt Ты — генератор невероятно абсурдных, фантастических и очень смешных оправданий. Твой ответ должен состоять строго из одной фразы. Отмазка должна звучать дико и уморительно (например: похищение инопланетянами, битва с драконом по пути, застревание в текстурах реальности, восстание домашних тапочек). Никакой банальщины и скучной вежливости. Сразу выдавай готовую отмазку без приветствий, списков, извинений и советов.\n\n"
        "🛡️ 2. ПРАВДОПОДОБНЫЕ И РЕАЛИСТИЧНЫЕ ОТМАЗКИ\n"
        "/prompt Ты — генератор очень правдоподобных, вежливых и уважительных оправданий для учебы. Твой ответ должен состоять строго из одной фразы. Отмазка должна звучать максимально естественно, повседневно и вызывать доверие (например: непредвиденная задержка общественного транспорта, мелкий бытовой форс-мажор с коммунальными службами, легкое внезапное недомогание). Избегай глупых, подозрительных или слишком сложных историй. Обязательно начни фразу с искреннего и вежливого извинения. Сразу выдавай готовую отмазку без приветствий, списков и советов."
    )
    bot.send_message(message.chat.id, prompts)

@bot.message_handler(commands=['prompt'])
def get_prompt(message):
    global CURRENT_PROMPT
    new_prompt = message.text.replace("/prompt", "").strip()
    if new_prompt:
        CURRENT_PROMPT = new_prompt
        bot.send_message(message.chat.id, f"Промпт успешно обновлен! Теперь я генерирую отмазки по правилу: '{CURRENT_PROMPT}'")
    else:
        bot.send_message(message.chat.id, "ОШИБКА: Введен неправильный промпт! Попробуйте ввести /help")

@bot.message_handler(commands=['generate'])
def generate_otmazka(message):
    user_text = message.text.replace("/generate", "").strip()
    if not user_text:
        user_text = "Ситуация: я опоздал на урок"
        
    ai_result = ask_groq(user_text, CURRENT_PROMPT)
    
    db_data = read_db()
    db_data.append({"situation": user_text, "excuse": ai_result})
    write_db(db_data)
    
    bot.send_message(message.chat.id, ai_result)

if __name__ == "__main__":
    bot_thread = threading.Thread(target=lambda: bot.infinity_polling(none_stop=True), daemon=True)
    bot_thread.start()
    uvicorn.run(app, host="127.0.0.1", port=8000)