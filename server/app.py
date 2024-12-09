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
logging.info(f"YOUR_OPENAI_API_KEY: {(openai.api_key)}")
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
from datetime import datetime

# Функция поиска туров с датой в прошлом
def search_tours(destination):
    try:
        # Получение текущей даты в формате YYYY-MM-DD
        current_date = datetime.now().strftime("%Y-%m-%d")

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        query = """
            SELECT * FROM tours
            WHERE destination LIKE ?
            AND start_date > ?
        """
        cursor.execute(query, (f"%{destination}%", current_date))
        results = cursor.fetchall()
        conn.close()
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


# Маршрут для бронирования туров по ID
@app.route("/book_by_id", methods=["POST"])
def book_tour_by_id():
    data = request.json
    tour_id = data.get("tour_id")
    customer_name = data.get("customer_name")

    if not tour_id:
        return jsonify({"error": "Необходимо указать ID тура"}), 400

    # Если имя клиента не предоставлено, генерируем его
    if not customer_name:
        customer_name = generate_unique_customer_id()

    try:
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        # Получаем информацию о туре
        cursor.execute("SELECT destination, price, start_date, end_date FROM tours WHERE id = ?", (tour_id,))
        tour_info = cursor.fetchone()

        if not tour_info:
            conn.close()
            return jsonify({"error": "Тур с указанным ID не найден"}), 404

        destination, price, start_date, end_date = tour_info

        # Выполняем бронирование
        cursor.execute(
            "INSERT INTO bookings (tour_id, customer_name, status) VALUES (?, ?, ?)",
            (tour_id, customer_name, "confirmed"),
        )
        booking_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return jsonify({
            "message": "Бронирование успешно оформлено!",
            "booking_details": {
                "booking_id": booking_id,
                "customer_name": customer_name,
                "tour_details": {
                    "tour_id": tour_id,
                    "destination": destination,
                    "price": price,
                    "start_date": start_date,
                    "end_date": end_date
                }
            }
        }), 200
    except Exception as e:
        logging.error(f"Ошибка при бронировании: {e}")
        return jsonify({"error": f"Ошибка при оформлении бронирования: {e}"}), 500



from datetime import datetime
import sqlite3
import logging
import re

import hashlib
import time
import random
import json


# Генерация уникального идентификатора клиента
def generate_unique_customer_id():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    while True:
        unique_seed = f"{time.time()}-{random.randint(1000, 9999)}"
        customer_id = f"Client-{hashlib.md5(unique_seed.encode()).hexdigest()[:8]}"
        cursor.execute("SELECT * FROM bookings WHERE customer_name = ?", (customer_id,))
        if not cursor.fetchone():
            conn.close()
            return customer_id


def generate_unique_customer_id():
    import uuid
    return f"Client-{uuid.uuid4().hex[:8]}"



# Основной метод для бронирования тура
def map_quality(quality_str):
    if not quality_str:
        return None
    quality_str = quality_str.lower()
    if any(word in quality_str for word in ['высок', 'люкс', 'премиум', 'high', 'luxury', 'premium']):
        return 'high'
    elif any(word in quality_str for word in ['средн', 'стандарт', 'normal', 'middle', 'standard']):
        return 'middle'
    elif any(word in quality_str for word in ['низк', 'эконом', 'бюджет', 'low', 'economy', 'budget', 'cheap', 'not']):
        return 'low'
    else:
        return None



@app.route("/book", methods=["POST"])
def book_tour_by_message():
    data = request.json
    message = data.get("message", "")

    if not message:
        return jsonify({"error": "Сообщение клиента отсутствует."}), 400

    try:
        # Используем OpenAI для извлечения информации в формате JSON
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "Ты - помощник турагентства. Пожалуйста, извлеки информацию о туре и верни её в формате JSON: {\"destination\": \"страна\", \"price\": \"сумма или 'цена не указана'\", \"start_date\": \"YYYY-MM-DD\", \"end_date\": \"YYYY-MM-DD\", \"quality\": \"качество или 'не указано'\"}.",
                },
                {"role": "user", "content": message},
            ],
            max_tokens=200,
            temperature=0.7,
        )

        extracted_info = response["choices"][0]["message"]["content"]
        logging.info(f"Извлеченные данные от OpenAI: {extracted_info}")

        # Пробуем загрузить данные как JSON
        try:
            info = json.loads(extracted_info)
        except json.JSONDecodeError:
            logging.error("Не удалось разобрать ответ от OpenAI как JSON")
            return jsonify({"error": f"Пожалуйста, уточните запрос о конкретном туре в {destination}."}), 400

        # Проверяем обязательные поля
        required_fields = ['destination', 'start_date']
        missing = [field for field in required_fields if field not in info]
        if missing:
            return jsonify({"error": f"Не хватает обязательной информации: {', '.join(missing)}"}), 400

        destination = info['destination'].capitalize()

        # Преобразование цены с учетом возможного отсутствия
        price_str = info['price'].lower()
        if price_str == "цена не указана" or not price_str:
            price = None
        else:
            try:
                price = float(price_str.replace(' euro', '').replace(',', '.').strip())
            except ValueError:
                return jsonify({"error": "Неверный формат цены."}), 400

        start_date = info['start_date']

        # Проверка формата даты
        try:
            datetime.strptime(start_date, "%Y-%m-%d")
        except ValueError:
            return jsonify({"error": "Укажите, пожалуйста, конкретную дату начала тура в {}.".format(destination)}), 400

        end_date = info.get('end_date')
        quality = info.get('quality')

        logging.info(f"Парсинг успешен: Направление={destination}, Цена={price}, Начало={start_date}, Конец={end_date}, Качество={quality}")

        # Подключаемся к базе данных и ищем подходящие туры
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        # Получаем текущую дату
        current_date = datetime.now().date()

        query = """
            SELECT id, destination, price, quality, start_date, end_date
            FROM tours
            WHERE destination = ?
            AND start_date = ?
            AND start_date >= ?
        """

        params = [destination, start_date, current_date.strftime("%Y-%m-%d")]

        if price is not None:
            query += " AND price = ?"
            params.append(price)

        cursor.execute(query, params)
        tours = cursor.fetchall()

        if not tours:
            conn.close()
            return jsonify({"error": "К сожалению, подходящих туров не найдено. Пожалуйста, уточните параметры запроса или укажите ID конкретного тура."}), 404

        if len(tours) > 1:
            # Если найдено несколько туров, возвращаем информацию для уточнения
            tour_details = [
                f"Тур ID={tour[0]}: направление {tour[1]}, цена {tour[2]}, качество {tour[3]}, даты {tour[4]} - {tour[5]}"
                for tour in tours
            ]
            return jsonify({
                "message": "Найдено несколько подходящих туров. Пожалуйста, укажите ID конкретного тура для бронирования:",
                "tours": tour_details
            }), 300

        selected_tour = tours[0]
        tour_id, actual_destination, actual_price, actual_quality, actual_start_date, actual_end_date = selected_tour

        # Генерируем уникальный идентификатор клиента
        customer_id = generate_unique_customer_id()

        # Записываем бронирование в базу данных
        cursor.execute(
            "INSERT INTO bookings (tour_id, customer_name, status) VALUES (?, ?, ?)",
            (tour_id, customer_id, "confirmed"),
        )

        conn.commit()
        conn.close()

        return jsonify({
            "message": f"Бронирование успешно оформлено! Ваш идентификатор клиента: {customer_id}",
            "tour_details": {
                "destination": actual_destination,
                "price": actual_price,
                "start_date": actual_start_date,
                "end_date": actual_end_date,
                "quality": actual_quality
            },
        }), 200

    except Exception as e:
        logging.error(f"Ошибка при бронировании: {e}")
        return jsonify({"error": "Произошла ошибка при обработке запроса. Пожалуйста, попробуйте позже."}), 500



def generate_unique_customer_id():
    import uuid
    return f"Client-{uuid.uuid4().hex[:8]}"




if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
