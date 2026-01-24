-- Telemetry Store Database Initialization
-- Эти таблицы также создаются автоматически через SQLAlchemy ORM,
-- но этот скрипт служит в качестве документации схемы БД

-- Телеметрия устройств (временные ряды)
CREATE TABLE IF NOT EXISTS telemetry_data (
    id UUID PRIMARY KEY,
    external_device_id UUID NOT NULL,
    metric VARCHAR NOT NULL,
    value VARCHAR NOT NULL,
    recorded_at TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_telemetry_device ON telemetry_data(external_device_id);
CREATE INDEX IF NOT EXISTS idx_telemetry_metric ON telemetry_data(metric);
CREATE INDEX IF NOT EXISTS idx_telemetry_recorded ON telemetry_data(recorded_at DESC);
CREATE INDEX IF NOT EXISTS idx_telemetry_device_metric ON telemetry_data(external_device_id, metric, recorded_at DESC);

-- Комментарии
COMMENT ON TABLE telemetry_data IS 'Хранилище телеметрии устройств (временные ряды)';
COMMENT ON COLUMN telemetry_data.metric IS 'Тип метрики (temperature, humidity, power и т.д.)';
COMMENT ON COLUMN telemetry_data.value IS 'Значение метрики в строковом виде';
COMMENT ON COLUMN telemetry_data.recorded_at IS 'Время фиксации измерения устройством';

-- Для продакшна рекомендуется использовать TimescaleDB или InfluxDB
-- Этот скрипт показывает базовую схему для MVP на PostgreSQL
