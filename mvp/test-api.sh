#!/bin/bash

# Скрипт для тестирования API микросервисов WarmHome MVP
# Использование: ./test-api.sh

set -e

echo "================================"
echo "WarmHome MVP API Testing Script"
echo "================================"
echo ""

# Цвета для вывода
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Функция для проверки health endpoints
check_health() {
    echo -e "${YELLOW}1. Проверка здоровья сервисов...${NC}"
    
    services=("device-registry:8001" "command-service:8002" "telemetry-ingest:8003" "telemetry-query:8004")
    
    for service in "${services[@]}"; do
        name=$(echo $service | cut -d':' -f1)
        port=$(echo $service | cut -d':' -f2)
        
        echo -n "  Checking $name... "
        response=$(curl -s http://localhost:$port/health)
        if echo $response | grep -q "healthy"; then
            echo -e "${GREEN}✓ OK${NC}"
        else
            echo -e "${RED}✗ FAILED${NC}"
            echo "    Response: $response"
        fi
    done
    echo ""
}

# Функция для получения каталога моделей
get_device_models() {
    echo -e "${YELLOW}2. Получение каталога моделей устройств...${NC}"
    response=$(curl -s http://localhost:8001/api/v1/device-models)
    echo "$response" | jq '.'
    
    # Сохранение ID первой модели
    DEVICE_MODEL_ID=$(echo "$response" | jq -r '.[0].id')
    echo -e "${GREEN}Model ID для тестов: $DEVICE_MODEL_ID${NC}"
    echo ""
}

# Функция для регистрации устройства
register_device() {
    echo -e "${YELLOW}3. Регистрация нового устройства...${NC}"
    
    DEVICE_DATA='{
        "deviceModelId": "'$DEVICE_MODEL_ID'",
        "serialNumber": "TEST-SENSOR-001",
        "displayName": "Тестовый датчик температуры",
        "externalHouseId": "2b7a7a40-9e8e-4e9f-8d91-6f6a8f3d3a12",
        "externalZoneId": "c11f1e6c-b6cc-4c2a-9c01-7f51c1a12f9d"
    }'
    
    response=$(curl -s -X POST http://localhost:8001/api/v1/devices \
        -H "Content-Type: application/json" \
        -d "$DEVICE_DATA")
    
    echo "$response" | jq '.'
    
    # Сохранение ID устройства
    DEVICE_ID=$(echo "$response" | jq -r '.id')
    echo -e "${GREEN}Device ID: $DEVICE_ID${NC}"
    echo ""
}

# Функция для отправки телеметрии
send_telemetry() {
    echo -e "${YELLOW}4. Отправка телеметрии от устройства...${NC}"
    
    for i in {1..3}; do
        TEMP=$((20 + i))
        TELEMETRY_DATA='{
            "deviceId": "'$DEVICE_ID'",
            "metric": "temperature",
            "value": "'$TEMP'.5"
        }'
        
        echo "  Отправка измерения #$i: ${TEMP}.5°C"
        curl -s -X POST http://localhost:8003/api/v1/telemetry/ingest \
            -H "Content-Type: application/json" \
            -d "$TELEMETRY_DATA" | jq '.'
        
        sleep 1
    done
    echo ""
}

# Функция для получения телеметрии
get_telemetry() {
    echo -e "${YELLOW}5. Получение телеметрии устройства...${NC}"
    echo "  Ожидание обработки данных..."
    sleep 3
    
    response=$(curl -s "http://localhost:8004/api/v1/devices/$DEVICE_ID/telemetry?limit=5")
    echo "$response" | jq '.'
    echo ""
}

# Функция для получения последнего значения
get_latest_telemetry() {
    echo -e "${YELLOW}6. Получение последнего значения метрики...${NC}"
    response=$(curl -s "http://localhost:8004/api/v1/devices/$DEVICE_ID/telemetry/latest?metric=temperature")
    echo "$response" | jq '.'
    echo ""
}

# Функция для получения состояния устройства
get_device_state() {
    echo -e "${YELLOW}7. Получение состояния устройства...${NC}"
    echo "  Ожидание обновления состояния..."
    sleep 2
    
    response=$(curl -s "http://localhost:8001/api/v1/devices/$DEVICE_ID/state")
    echo "$response" | jq '.'
    echo ""
}

# Функция для отправки команды
send_command() {
    echo -e "${YELLOW}8. Отправка команды устройству...${NC}"
    
    COMMAND_DATA='{
        "commandType": "SET_TEMPERATURE_THRESHOLD",
        "payload": {
            "threshold": 25,
            "action": "alert"
        }
    }'
    
    response=$(curl -s -X POST "http://localhost:8002/api/v1/devices/$DEVICE_ID/commands" \
        -H "Content-Type: application/json" \
        -d "$COMMAND_DATA")
    
    echo "$response" | jq '.'
    
    # Сохранение ID команды
    COMMAND_ID=$(echo "$response" | jq -r '.id')
    echo -e "${GREEN}Command ID: $COMMAND_ID${NC}"
    echo ""
}

# Функция для проверки статуса команды
check_command_status() {
    echo -e "${YELLOW}9. Проверка статуса команды...${NC}"
    echo "  Ожидание выполнения команды (симуляция 2 сек)..."
    sleep 3
    
    response=$(curl -s "http://localhost:8002/api/v1/commands/$COMMAND_ID")
    echo "$response" | jq '.'
    echo ""
}

# Функция для получения статистики
get_stats() {
    echo -e "${YELLOW}10. Получение статистики телеметрии...${NC}"
    response=$(curl -s "http://localhost:8004/internal/stats")
    echo "$response" | jq '.'
    echo ""
}

# Основной поток выполнения
main() {
    # Проверка наличия jq
    if ! command -v jq &> /dev/null; then
        echo -e "${RED}Ошибка: jq не установлен. Установите: brew install jq${NC}"
        exit 1
    fi
    
    # Проверка наличия curl
    if ! command -v curl &> /dev/null; then
        echo -e "${RED}Ошибка: curl не установлен${NC}"
        exit 1
    fi
    
    echo "Начинаем тестирование API..."
    echo ""
    
    check_health
    get_device_models
    register_device
    send_telemetry
    get_telemetry
    get_latest_telemetry
    get_device_state
    send_command
    check_command_status
    get_stats
    
    echo -e "${GREEN}================================${NC}"
    echo -e "${GREEN}Тестирование завершено успешно!${NC}"
    echo -e "${GREEN}================================${NC}"
    echo ""
    echo "Swagger документация доступна по адресам:"
    echo "  - Device Registry: http://localhost:8001/docs"
    echo "  - Command Service: http://localhost:8002/docs"
    echo "  - Telemetry Ingest: http://localhost:8003/docs"
    echo "  - Telemetry Query: http://localhost:8004/docs"
}

# Запуск
main
