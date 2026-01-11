# Руководство по Интеграции MVP Микросервисов с Монолитом

## 📦 Созданные компоненты

### API Gateway (`:8000`) ⭐

**Единая точка входа** для всех микросервисов:
- **Функции**:
  - Проксирование всех запросов к микросервисам
  - Мониторинг здоровья всех сервисов
  - Централизованная обработка ошибок
  - Упрощение интеграции (один URL вместо четырех)
- **Файлы**:
  - [`api-gateway/main.py`](api-gateway/main.py)
  - [`api-gateway/Dockerfile`](api-gateway/Dockerfile)
  - [`api-gateway/requirements.txt`](api-gateway/requirements.txt)

**Health Check:**
```bash
curl http://localhost:8000/health
# Ответ включает статус всех микросервисов
```

**Swagger документация:** http://localhost:8000/docs

### Микросервисы (все на Python/FastAPI)

#### 1. Device Registry Service (`:8001`)
- **Функции**: Управление устройствами и их моделями
- **База данных**: PostgreSQL `device_registry`
- **Файлы**: 
  - [`device-registry/main.py`](device-registry/main.py)
  - [`device-registry/Dockerfile`](device-registry/Dockerfile)
  - [`device-registry/requirements.txt`](device-registry/requirements.txt)

**Основные endpoints:**
- `GET /api/v1/device-models` - каталог моделей устройств
- `POST /api/v1/devices` - регистрация устройства
- `GET /api/v1/devices/{id}` - получение информации об устройстве
- `GET /api/v1/devices/{id}/state` - получение состояния устройства
- `PUT /api/v1/devices/{id}/state` - обновление состояния (внутренний)

#### 2. Command Service (`:8002`)
- **Функции**: Управление командами устройствам
- **База данных**: PostgreSQL `command_service`
- **Файлы**: 
  - [`command-service/main.py`](command-service/main.py)
  - [`command-service/Dockerfile`](command-service/Dockerfile)
  - [`command-service/requirements.txt`](command-service/requirements.txt)

**Основные endpoints:**
- `POST /api/v1/devices/{id}/commands` - отправка команды устройству
- `GET /api/v1/commands/{id}` - получение статуса команды
- `GET /api/v1/devices/{id}/commands` - список команд для устройства

#### 3. Telemetry Ingest Service (`:8003`)
- **Функции**: Прием и нормализация телеметрии от устройств
- **База данных**: PostgreSQL `telemetry_store` (общая с Telemetry Query)
- **Файлы**: 
  - [`telemetry-ingest/main.py`](telemetry-ingest/main.py)
  - [`telemetry-ingest/Dockerfile`](telemetry-ingest/Dockerfile)
  - [`telemetry-ingest/requirements.txt`](telemetry-ingest/requirements.txt)

**Основные endpoints:**
- `POST /api/v1/telemetry/ingest` - прием телеметрии
- `GET /internal/telemetry-events` - просмотр событий (отладка)
- `GET /internal/state-events` - просмотр событий состояния (отладка)

#### 4. Telemetry Query Service (`:8004`)
- **Функции**: Чтение телеметрии и исторических данных
- **База данных**: PostgreSQL `telemetry_store` (общая с Telemetry Ingest)
- **Файлы**: 
  - [`telemetry-query/main.py`](telemetry-query/main.py)
  - [`telemetry-query/Dockerfile`](telemetry-query/Dockerfile)
  - [`telemetry-query/requirements.txt`](telemetry-query/requirements.txt)

**Основные endpoints:**
- `GET /api/v1/devices/{id}/telemetry` - получение телеметрии устройства
- `GET /api/v1/devices/{id}/telemetry/latest` - последнее значение метрики
- `GET /api/v1/telemetry` - телеметрия всех устройств
- `GET /internal/stats` - статистика хранилища

### Инфраструктура

#### Базы данных
1. **registry-db** (порт 5432)
   - БД: `device_registry`
   - Init скрипт: [`init-scripts/01-device-registry-init.sql`](init-scripts/01-device-registry-init.sql)
   - Таблицы: `device_models`, `devices`, `device_states`

2. **command-db** (порт 5433)
   - БД: `command_service`
   - Init скрипт: [`init-scripts/02-command-service-init.sql`](init-scripts/02-command-service-init.sql)
   - Таблицы: `commands`

3. **telemetry-db** (порт 5434)
   - БД: `telemetry_store`
   - Init скрипт: [`init-scripts/03-telemetry-store-init.sql`](init-scripts/03-telemetry-store-init.sql)
   - Таблицы: `telemetry_data`

#### Дополнительные файлы
- [`docker-compose.yml`](docker-compose.yml) - оркестрация всех сервисов
- [`test-api.sh`](test-api.sh) - автоматическое тестирование API
- [`README.md`](README.md) - полная документация

## 🔄 Интеграция с Монолитом

### Текущая архитектура монолита

Монолит на Go (в `apps/smart_home/`) имеет следующую структуру:
- **Порт**: 8080
- **База данных**: PostgreSQL `smarthome`
- **Основной функционал**: Управление сенсорами
- **Интеграция**: С внешним Temperature API

### Стратегия миграции: Strangler Fig Pattern

#### Этап 1: Независимое сосуществование
```
┌─────────────────┐
│ Монолит         │──► Собственная БД
│ (Go, :8080)     │──► Temperature API
└─────────────────┘

┌──────────────────────────────────────┐
│ API Gateway (:8000)                  │
└──────────────────────────────────────┘
    │
    ├──► Device Registry    ──► PostgreSQL
    ├──► Command Service    ──► PostgreSQL
    ├──► Telemetry Ingest   ──► PostgreSQL
    └──► Telemetry Query    ──► (shared)
```

Монолит и микросервисы работают независимо. API Gateway уже настроен.

#### Этап 2: Частичная миграция (рекомендуемый следующий шаг)
```
                    ┌─────────────────┐
          ┌─────────┤ Монолит         │──► Собственная БД
          │         │ (Go, :8080)     │
          │         └─────────────────┘
          │ Делегирует
          │ некоторые запросы
          ▼
┌──────────────────────────────────────┐
│ API Gateway (:8000)                  │ ⭐ Единая точка входа
└──────────────────────────────────────┘
    │
    ├──► Device Registry    ──► PostgreSQL
    ├──► Command Service    ──► PostgreSQL
    ├──► Telemetry Ingest   ──► PostgreSQL
    └──► Telemetry Query    ──► (shared)
```

Монолит постепенно делегирует функции через API Gateway:
- Начать с чтения данных (телеметрия)
- Затем регистрация устройств
- Далее команды управления

#### Этап 3: Полная миграция (целевая)
```
         ┌─────────────────────┐
         │  Пользователи       │
         │  (Web/Mobile)       │
         └─────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────┐
│ API Gateway (:8000)                  │
│ + Аутентификация                     │
│ + Rate Limiting                      │
│ + Мониторинг                         │
└──────────────────────────────────────┘
       │
   ┌───┴────┬────────┬─────────┐
   ▼        ▼        ▼         ▼
┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐
│Device│ │Telem.│ │Telem.│ │Cmd   │
│Reg.  │ │Ingest│ │Query │ │Svc   │
└──────┘ └──────┘ └──────┘ └──────┘
   │        │        │         │
   ▼        ▼        ▼         ▼
  DB1      DB3      DB3       DB2
```

Монолит полностью заменен микросервисами, доступ только через API Gateway.

### Точки интеграции

**Рекомендуется**: Все запросы от монолита направлять через **API Gateway** (`:8000`) для упрощения интеграции.

#### 1. Регистрация устройств

**Монолит → API Gateway:**
```http
POST http://api-gateway:8000/api/v1/devices
Content-Type: application/json

{
  "deviceModelId": "7d7c8e0b-8f41-4f3c-9d9c-0f2b3b2c1d10",
  "serialNumber": "SENSOR-001",
  "displayName": "Датчик температуры",
  "externalHouseId": "uuid-дома",
  "externalZoneId": "uuid-зоны"
}
```

<details>
<summary>Альтернатива: прямой доступ к Device Registry</summary>

```http
POST http://device-registry:8001/api/v1/devices
```
</details>

#### 2. Отправка телеметрии

**Монолит → API Gateway:**
```http
POST http://api-gateway:8000/api/v1/telemetry/ingest
Content-Type: application/json

{
  "deviceId": "uuid-устройства",
  "metric": "temperature",
  "value": "22.5"
}
```

<details>
<summary>Альтернатива: прямой доступ к Telemetry Ingest</summary>

```http
POST http://telemetry-ingest:8003/api/v1/telemetry/ingest
```
</details>

#### 3. Чтение телеметрии

**Монолит → API Gateway:**
```http
GET http://api-gateway:8000/api/v1/devices/{deviceId}/telemetry?limit=10
```

<details>
<summary>Альтернатива: прямой доступ к Telemetry Query</summary>

```http
GET http://telemetry-query:8004/api/v1/devices/{deviceId}/telemetry?limit=10
```
</details>

#### 4. Управление устройствами

**Монолит → API Gateway:**
```http
POST http://api-gateway:8000/api/v1/devices/{deviceId}/commands
Content-Type: application/json

{
  "commandType": "SET_TEMPERATURE",
  "payload": {
    "value": 25
  }
}
```

<details>
<summary>Альтернатива: прямой доступ к Command Service</summary>

```http
POST http://command-service:8002/api/v1/devices/{deviceId}/commands
```
</details>

## 📝 Следующие шаги

### Краткосрочные (MVP → Production)
1. ✅ Создание микросервисов
2. ✅ Настройка БД и Docker Compose
3. ✅ API Gateway (единая точка входа)
4. ⬜ Добавление HTTP клиентов в монолит
5. ⬜ Постепенная миграция функциональности
6. ⬜ Добавление реального брокера сообщений (Kafka/RabbitMQ)