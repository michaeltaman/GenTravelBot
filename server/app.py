from flask import Flask, request, jsonify
import sqlite3
import os
from dotenv import load_dotenv
import openai

import logging

# Настройка логирования
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

# Загрузка переменных окружения
load_dotenv()

app = Flask(__name__)

# Установите ваш API-ключ OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")
logging.info(f"API Key Loaded: {bool(openai.api_key)}")

# Загрузка инструкции
try:
    with open("instruction.txt", "r", encoding="utf-8") as f:
        instruction = f.read()
        logging.info("Instruction file loaded successfully.")
except FileNotFoundError:
    logging.error("Instruction file not found.")
    instruction = ""

# Функция поиска туров в базе данных
def search_tours(destination):
    try:
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        query = "SELECT * FROM tours WHERE destination LIKE ?"
        cursor.execute(query, (f"%{destination}%",))
        results = cursor.fetchall()
        conn.close()
        logging.info(f"Tours found for destination '{destination}': {len(results)}")
        return results
    except Exception as e:
        logging.error(f"Ошибка при поиске туров: {e}")
        return []

# Генерация ответа с использованием OpenAI
def generate_response(user_input, tours):
    try:
        tours_info = "\n".join([
            f"Тур: {tour[1]}, Цена: {tour[2]}$, Качество: {tour[3]}, Даты: {tour[4]} - {tour[5]}"
            for tour in tours
        ])
        prompt = f"{instruction}\n\nЗапрос клиента: {user_input}\n\nДоступные туры:\n{tours_info if tours else 'Нет подходящих туров.'}"
        logging.debug(f"Generated prompt: {prompt}")

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": instruction},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7, # чтобы модель была более креативной и разнообразной.
            max_tokens=500,
        )
        tokens_used = response['usage']['total_tokens']
        logging.info(f"OpenAI API call successful. Tokens used: {tokens_used}")
        return response["choices"][0]["message"]["content"]

    except openai.error.OpenAIError as e:
        logging.error(f"Ошибка OpenAI API: {e}")
        return f"Произошла ошибка OpenAI: {e}"
    except Exception as e:
        logging.error(f"Неизвестная ошибка: {e}")
        return "Произошла ошибка. Пожалуйста, попробуйте позже."

# Маршрут для обработки запросов
@app.route("/process", methods=["POST"])
def process_request():
    try:
        data = request.json
        user_input = data.get("message", "")
        destination = data.get("destination", "")

        logging.info(f"Запрос: {user_input}, Направление: {destination}")

        # Поиск туров
        tours = search_tours(destination)

        # Генерация ответа
        response = generate_response(user_input, tours)
        return jsonify({"response": response})
    except Exception as e:
        logging.error(f"Ошибка: {e}")
        return jsonify({"error": "Произошла ошибка. Пожалуйста, попробуйте позже."}), 500


# Маршрут для бронирования туров
@app.route("/book", methods=["POST"])
def book_tour():
    data = request.json
    tour_id = data.get("tour_id")
    customer_name = data.get("customer_name")

    if not tour_id or not customer_name:
        return jsonify({"error": "Необходимо указать ID тура и имя клиента"}), 400

    try:
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO bookings (tour_id, customer_name, status) VALUES (?, ?, ?)",
            (tour_id, customer_name, "confirmed"),
        )
        conn.commit()
        conn.close()
        return jsonify({"message": "Бронирование успешно оформлено!"}), 200
    except Exception as e:
        logging.error(f"Ошибка при бронировании: {e}")
        return jsonify({"error": f"Ошибка при оформлении бронирования: {e}"}), 500


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
