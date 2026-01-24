-- Device Registry Database Initialization
-- Эти таблицы также создаются автоматически через SQLAlchemy ORM,
-- но этот скрипт служит в качестве документации схемы БД

-- Модели устройств (справочник)
CREATE TABLE IF NOT EXISTS device_models (
    id UUID PRIMARY KEY,
    name VARCHAR NOT NULL,
    device_type VARCHAR NOT NULL,
    protocol VARCHAR NOT NULL
);

-- Устройства
CREATE TABLE IF NOT EXISTS devices (
    id UUID PRIMARY KEY,
    device_model_id UUID NOT NULL,
    serial_number VARCHAR UNIQUE NOT NULL,
    display_name VARCHAR NOT NULL,
    external_house_id UUID NOT NULL,
    external_zone_id UUID,
    installed_at TIMESTAMP,
    status VARCHAR DEFAULT 'offline',
    lifecycle_state VARCHAR DEFAULT 'provisioning',
    last_seen_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_devices_house ON devices(external_house_id);
CREATE INDEX IF NOT EXISTS idx_devices_serial ON devices(serial_number);

-- Состояния устройств
CREATE TABLE IF NOT EXISTS device_states (
    id UUID PRIMARY KEY,
    device_id UUID UNIQUE NOT NULL,
    state TEXT NOT NULL,  -- JSON
    updated_at TIMESTAMP NOT NULL,
    source VARCHAR NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_device_states_device ON device_states(device_id);

-- Комментарии
COMMENT ON TABLE device_models IS 'Каталог моделей устройств';
COMMENT ON TABLE devices IS 'Зарегистрированные физические устройства';
COMMENT ON TABLE device_states IS 'Последнее известное состояние каждого устройства';
