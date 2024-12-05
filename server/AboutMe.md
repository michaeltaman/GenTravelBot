
# Сборка и тестирование Docker-образа

## 1. Собери образ Docker:

```bash
docker build -t tourgptagent .
```

## 2. Запусти контейнер:

## a) Использование абсолютного пути
   Укажи полный путь к файлу database.db. Например:
```bash
docker run -d -p 5000:5000 --name tourgptagent -v D:/sources/Investigations/TourGPTAgent/database.db:/app/database.db tourgptagent
```
## b) Использование ${PWD} в PowerShell
 PowerShell поддерживает переменную ${PWD} для текущей директории:
```bash
docker run -d -p 5000:5000 --name tourgptagent --env-file D:/sources/Investigations/TourGPTAgent/.env -v D:/sources/Investigations/TourGPTAgent/database.db:/app/database.db tourgptagent
```

## 3. Проверь работу сервиса:

Отправь запрос на `http://localhost:5000/process` с Postman или curl:

```json
{
    "message": "Я хочу тур в Швейцарию.",
    "destination": "Switzerland"
}
```

Убедись, что всё работает корректно.

## 4. Остановка контейнера

Когда тестирование завершено:

```bash
docker stop tourgptagent
docker rm tourgptagent
```



## 5. Проверка после запуска
После запуска:

Войди внутрь контейнера:

```bash
docker exec -it tourgptagent bash

## Проверь, загружена ли переменная:

```bash
echo $OPENAI_API_KEY
```
Ты должен увидеть ваш API-ключ.
PS D:\sources\Investigations\TourGPTAgent> docker exec -it tourgptagent bash

root@6e5b4bcec7e1:/app#curl -X POST http://127.0.0.1:5000/process \
-H "Content-Type: application/json" \
-d '{"message": "Я хочу тур в Italy.", "destination": "Italy"}'

## 6. Сеанс с базой данных
```bash
PS D:\sources\Investigations\TourGPTAgent> docker exec -it tourgptagent bash
root@23154efdf0a8:/app# sqlite3 database.db
SQLite version 3.40.1 2022-12-28 14:03:47
Enter ".help" for usage hints.
sqlite> SELECT * FROM tours;
1|Switzerland|1000.0|high|2024-12-15|2024-12-20
1|Switzerland|1000.0|high|2024-12-15|2024-12-20
2|France|800.0|medium|2024-12-10|2024-12-15
3|Italy|600.0|low|2024-12-05|2024-12-10
4|Switzerland|1000.0|high|2024-12-15|2024-12-20
5|France|800.0|medium|2024-12-10|2024-12-15
6|Italy|600.0|low|2024-12-05|2024-12-10
sqlite>.exit
```






