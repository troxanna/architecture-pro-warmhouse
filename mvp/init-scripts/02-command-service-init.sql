-- Command Service Database Initialization
-- Эти таблицы также создаются автоматически через SQLAlchemy ORM,
-- но этот скрипт служит в качестве документации схемы БД

-- Команды управления устройствами
CREATE TABLE IF NOT EXISTS commands (
    id UUID PRIMARY KEY,
    external_device_id UUID NOT NULL,
    command_type VARCHAR NOT NULL,
    payload TEXT,  -- JSON
    status VARCHAR DEFAULT 'pending',  -- pending|succeeded|failed
    created_at TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_commands_device ON commands(external_device_id);
CREATE INDEX IF NOT EXISTS idx_commands_status ON commands(status);
CREATE INDEX IF NOT EXISTS idx_commands_created ON commands(created_at DESC);

-- Комментарии
COMMENT ON TABLE commands IS 'Команды управления устройствами';
COMMENT ON COLUMN commands.status IS 'Статус выполнения: pending, succeeded, failed';
COMMENT ON COLUMN commands.payload IS 'Параметры команды в формате JSON';
