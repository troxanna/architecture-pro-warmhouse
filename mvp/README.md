# MVP Микросервисной Архитектуры WarmHome

Минимально жизнеспособный продукт (MVP) микросервисной архитектуры для системы "Тёплый дом", реализующий управление устройствами и телеметрией.

## 📋 Описание

MVP включает **API Gateway** и 4 микросервиса, каждый на Python с использованием FastAPI:

### API Gateway

**API Gateway** (порт 8000) - единая точка входа для всех микросервисов
- Проксирование запросов к микросервисам
- Мониторинг здоровья всех сервисов
- Централизованная обработка ошибок

### Микросервисы

1. **Device Registry Service** (порт 8001)
   - Управление устройствами и их моделями
   - Регистрация устройств и привязка к домам/зонам
   - Хранение последнего известного состояния устройств
   - БД: PostgreSQL (`device_registry`)

2. **Command Service** (порт 8002)
   - Прием и управление командами для устройств
   - Публикация команд в брокер сообщений (симулируется)
   - Отслеживание статуса выполнения команд
   - БД: PostgreSQL (`command_service`)

3. **Telemetry Ingest Service** (порт 8003)
   - Прием и нормализация телеметрии от устройств
   - Сохранение телеметрии в Time-series хранилище
   - Публикация событий обновления состояния устройств
   - БД: PostgreSQL (`telemetry_store`) - общая с Telemetry Query

4. **Telemetry Query Service** (порт 8004)
   - Чтение телеметрии и исторических данных
   - Фильтрация по устройствам, метрикам и временным диапазонам
   - Получение последних значений метрик
   - БД: PostgreSQL (`telemetry_store`) - общая с Telemetry Ingest

### Инфраструктура

- **3 PostgreSQL базы данных**:
  - `registry-db` (порт 5432): для Device Registry
  - `command-db` (порт 5433): для Command Service
  - `telemetry-db` (порт 5434): для Telemetry Ingest & Query

## 🚀 Быстрый старт

### Предварительные требования

- Docker
- Docker Compose
- curl (для тестирования API)

### Запуск всех сервисов

```bash
cd mvp
docker-compose up --build
```

Сервисы будут доступны на портах:
- **API Gateway: http://localhost:8000** ⭐ (единая точка входа)
- Device Registry: http://localhost:8001 (прямой доступ)
- Command Service: http://localhost:8002 (прямой доступ)
- Telemetry Ingest: http://localhost:8003 (прямой доступ)
- Telemetry Query: http://localhost:8004 (прямой доступ)

**Рекомендуется использовать API Gateway (порт 8000) для всех запросов.**

### Проверка здоровья сервисов

```bash
curl http://localhost:8001/health
curl http://localhost:8002/health
curl http://localhost:8003/health
curl http://localhost:8004/health
```

### Остановка сервисов

```bash
docker-compose down
```

Для удаления данных БД:
```bash
docker-compose down -v
```

### Автоматическое тестирование

Для автоматической проверки всех API используйте тестовый скрипт:

```bash
./test-api.sh
```

Скрипт выполнит:
1. Проверку здоровья всех сервисов
2. Получение каталога моделей устройств
3. Регистрацию тестового устройства
4. Отправку телеметрии (3 измерения)
5. Получение телеметрии устройства
6. Получение последнего значения
7. Получение состояния устройства
8. Отправку команды
9. Проверку статуса команды
10. Получение статистики

**Требования:** установите `jq` для форматирования JSON:
```bash
# macOS
brew install jq

# Ubuntu/Debian
sudo apt-get install jq
```

## 📚 Примеры использования API

### 1. Получение каталога моделей устройств

```bash
curl http://localhost:8001/api/v1/device-models
```

Ответ:
```json
[
  {
    "id": "7d7c8e0b-8f41-4f3c-9d9c-0f2b3b2c1d10",
    "name": "Temperature Sensor Model A",
    "device_type": "temperature_sensor",
    "protocol": "http"
  },
  {
    "id": "8e8d9f1c-9f52-4f4d-9e9d-1f3c4c3d2e21",
    "name": "Heat Relay Model B",
    "device_type": "relay",
    "protocol": "http"
  }
]
```

### 2. Регистрация устройства

```bash
curl -X POST http://localhost:8001/api/v1/devices \
  -H "Content-Type: application/json" \
  -d '{
    "deviceModelId": "7d7c8e0b-8f41-4f3c-9d9c-0f2b3b2c1d10",
    "serialNumber": "SENSOR-001",
    "displayName": "Датчик температуры в гостиной",
    "externalHouseId": "2b7a7a40-9e8e-4e9f-8d91-6f6a8f3d3a12",
    "externalZoneId": "c11f1e6c-b6cc-4c2a-9c01-7f51c1a12f9d"
  }'
```

Ответ (сохраните `id` устройства):
```json
{
  "id": "0cbf1a0a-9b83-4a4f-9b21-112233445566",
  "deviceModelId": "7d7c8e0b-8f41-4f3c-9d9c-0f2b3b2c1d10",
  "serialNumber": "SENSOR-001",
  "displayName": "Датчик температуры в гостиной",
  "externalHouseId": "2b7a7a40-9e8e-4e9f-8d91-6f6a8f3d3a12",
  "externalZoneId": "c11f1e6c-b6cc-4c2a-9c01-7f51c1a12f9d",
  "installedAt": "2026-01-11T10:00:00Z",
  "status": "offline",
  "lifecycleState": "provisioning",
  "lastSeenAt": null
}
```

### 3. Отправка телеметрии от устройства

```bash
curl -X POST http://localhost:8003/api/v1/telemetry/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "deviceId": "0cbf1a0a-9b83-4a4f-9b21-112233445566",
    "metric": "temperature",
    "value": "22.5"
  }'
```

Ответ:
```json
{
  "status": "accepted",
  "deviceId": "0cbf1a0a-9b83-4a4f-9b21-112233445566",
  "metric": "temperature"
}
```

### 4. Получение телеметрии устройства

```bash
curl "http://localhost:8004/api/v1/devices/0cbf1a0a-9b83-4a4f-9b21-112233445566/telemetry?limit=10"
```

Ответ:
```json
{
  "items": [
    {
      "id": "f1e2d3c4-b5a6-4f00-9a99-123456789000",
      "externalDeviceId": "0cbf1a0a-9b83-4a4f-9b21-112233445566",
      "metric": "temperature",
      "value": "22.5",
      "recordedAt": "2026-01-11T10:00:00Z"
    }
  ]
}
```

### 5. Получение последнего значения метрики

```bash
curl "http://localhost:8004/api/v1/devices/0cbf1a0a-9b83-4a4f-9b21-112233445566/telemetry/latest?metric=temperature"
```

Ответ:
```json
{
  "id": "f1e2d3c4-b5a6-4f00-9a99-123456789000",
  "externalDeviceId": "0cbf1a0a-9b83-4a4f-9b21-112233445566",
  "metric": "temperature",
  "value": "22.5",
  "recordedAt": "2026-01-11T10:00:00Z"
}
```

### 6. Получение состояния устройства

```bash
curl http://localhost:8001/api/v1/devices/0cbf1a0a-9b83-4a4f-9b21-112233445566/state
```

Ответ:
```json
{
  "id": "9d1b2f3a-1111-2222-3333-444455556666",
  "deviceId": "0cbf1a0a-9b83-4a4f-9b21-112233445566",
  "state": {
    "temperature": "22.5"
  },
  "updatedAt": "2026-01-11T10:00:00Z",
  "source": "telemetry"
}
```

### 7. Отправка команды устройству

```bash
curl -X POST http://localhost:8002/api/v1/devices/0cbf1a0a-9b83-4a4f-9b21-112233445566/commands \
  -H "Content-Type: application/json" \
  -d '{
    "commandType": "HEAT_RELAY_SET",
    "payload": {
      "enabled": true
    }
  }'
```

Ответ:
```json
{
  "id": "aa0c9e7d-0e7b-4c9d-9a2c-8e0a1d2b3c4d",
  "externalDeviceId": "0cbf1a0a-9b83-4a4f-9b21-112233445566",
  "commandType": "HEAT_RELAY_SET",
  "payload": {
    "enabled": true
  },
  "status": "pending",
  "createdAt": "2026-01-11T10:01:00Z"
}
```

### 8. Получение статуса команды

```bash
curl http://localhost:8002/api/v1/commands/aa0c9e7d-0e7b-4c9d-9a2c-8e0a1d2b3c4d
```

## 📊 Swagger документация

Каждый сервис предоставляет автоматическую OpenAPI документацию:

- **API Gateway: http://localhost:8000/docs** ⭐ (объединенная документация)
- Device Registry: http://localhost:8001/docs
- Command Service: http://localhost:8002/docs
- Telemetry Ingest: http://localhost:8003/docs
- Telemetry Query: http://localhost:8004/docs

## 🧪 Отладочные endpoints (только для MVP)

### Просмотр очереди команд (Command Service)
```bash
curl http://localhost:8002/internal/message-queue
```

### Просмотр событий телеметрии (Telemetry Ingest)
```bash
curl http://localhost:8003/internal/telemetry-events
curl http://localhost:8003/internal/state-events
```

### Статистика телеметрии (Telemetry Query)
```bash
curl http://localhost:8004/internal/stats
```

## 🔄 Сценарий взаимодействия микросервисов

1. **Device Registry** регистрирует устройство и создает начальное состояние
2. **Telemetry Ingest** принимает данные от устройства:
   - Сохраняет в Telemetry Store (PostgreSQL)
   - Публикует событие `device.state.updated` (симулируется)
3. **Device Registry** подписывается на события (в MVP симулируется) и обновляет состояние
4. **Telemetry Query** читает данные из Telemetry Store
5. **Command Service** принимает команды:
   - Сохраняет в БД
   - Публикует событие `command.created` (симулируется)
   - Симулирует выполнение через 2 секунды

## 🏷️ Упрощения для MVP

1. **Брокер сообщений**: Вместо Kafka используется in-memory симуляция
2. **Аутентификация**: Отсутствует (все запросы считаются доверенными)
3. **Мониторинг**: Только базовые health checks
4. **Time-series БД**: Используется PostgreSQL вместо InfluxDB/TimescaleDB
5. **Identity & Ownership Service**: Отсутствует
6. **Rules Service**: Отсутствует
7. **Protocol Adapter Service**: Отсутствует

## 📁 Структура проекта

```
mvp/
├── api-gateway/
│   ├── Dockerfile
│   ├── main.py
│   └── requirements.txt
├── device-registry/
│   ├── Dockerfile
│   ├── main.py
│   └── requirements.txt
├── command-service/
│   ├── Dockerfile
│   ├── main.py
│   └── requirements.txt
├── telemetry-ingest/
│   ├── Dockerfile
│   ├── main.py
│   └── requirements.txt
├── telemetry-query/
│   ├── Dockerfile
│   ├── main.py
│   └── requirements.txt
├── docker-compose.yml
└── README.md
```

