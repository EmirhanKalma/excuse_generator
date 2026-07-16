import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import FileResponse
import telebot
import requests
import threading
import uvicorn

load_dotenv()

app = FastAPI()

CURRENT_PROMPT = "Ты — генератор очень правдоподобных, вежливых и убедительных оправданий для учебы. Твой ответ должен состоять строго из одной фразы. Отмазка должна звучать максимально естественно, повседневно и вызывать доверие (например: задержка транспорта, мелкий бытовой форс-мажор, легкое физическое недомогание). Никакой фантастики и глупостей. Начни фразу с вежливого извинения. Не пиши никаких приветствий, списков, советов и лишних слов. Сразу выдавай готовую отмазку."

@app.get("/")
def home_page():
    return FileResponse("templates/index.html")

@app.get("/generate")
def generate_exuses():
    return FileResponse("templates/generate.html")

@app.post("/add-excuse")
def save_excuse():
    return {"message": "Отмазка сохранена"}

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    responce_text = "Привет! Я ОтмазкоГенератор 3000. Напиши мне команду /generate, чтобы получить отмазку. Если хочешь изменить правила генерации, напиши команду /prompt и твой текст."
    bot.send_message(message.chat.id, responce_text)

@bot.message_handler(commands=['prompt'])
def get_prompt(message):
    global CURRENT_PROMPT
    
    new_prompt = message.text.replace("/prompt", "").strip()
    
    if new_prompt:
        CURRENT_PROMPT = new_prompt
        bot.send_message(message.chat.id, f"Промпт успешно обновлен! Теперь я генерирую отмазки по правилу: '{CURRENT_PROMPT}'")
    else:
        bot.send_message(message.chat.id, "Вы ввели пустой промпт! Напишите команду вот так, например:\n/prompt Сделай отмазку максимально смешной и глупой")

@bot.message_handler(commands=['generate'])
def generate_otmazka(message):
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    API_URL = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    def ask_ai_for_excuse(prompt_text):
        payload = {
            "model": "llama-3.1-8b-instant",
            "messages": [
                {
                    "role": "system",
                    "content": CURRENT_PROMPT
                },
                {
                    "role": "user",
                    "content": prompt_text
                }
            ],
            "temperature": 0.8
        }
        response = requests.post(API_URL, headers=headers, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            ai_response = result['choices'][0]['message']['content']
            return ai_response
        else:
            print(f"Ошибка ИИ: {response.status_code}, {response.text}")
            return "Мой кот съел кабель интернета, поэтому я не смог сгенерировать отмазку."

    user_text = message.text.replace("/generate", "").strip()
    
    if not user_text:
        user_text = "Ситуация: я опоздал на урок"

    ai_result = ask_ai_for_excuse(user_text)
    bot.send_message(message.chat.id, ai_result)

if __name__ == "__main__":
    bot_thread = threading.Thread(target=lambda: bot.infinity_polling(none_stop=True), daemon=True)
    bot_thread.start()
    uvicorn.run(app, host="127.0.0.1", port=8000)