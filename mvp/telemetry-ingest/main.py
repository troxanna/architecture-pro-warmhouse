"""
Telemetry Ingest Service
Микросервис для приема и нормализации телеметрии от устройств
"""
from fastapi import FastAPI, HTTPException, status, BackgroundTasks, Depends
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID, uuid4
import uvicorn
import os
from sqlalchemy import create_engine, Column, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.dialects.postgresql import UUID as PGUUID

# ========== Configuration ==========
TELEMETRY_DATABASE_URL = os.getenv("TELEMETRY_DATABASE_URL", "postgresql://warmhouse:warmhouse@telemetry-db:5432/telemetry_store")

# ========== Database Configuration ==========
engine = create_engine(TELEMETRY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ========== Database Models ==========

class TelemetryDataDB(Base):
    __tablename__ = "telemetry_data"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    external_device_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    metric = Column(String, nullable=False, index=True)
    value = Column(String, nullable=False)
    recorded_at = Column(DateTime, nullable=False, index=True)


# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Telemetry Ingest Service", version="1.0.0")


# ========== Pydantic Models ==========

class TelemetryRecordedEvent(BaseModel):
    """Событие о получении телеметрии (из брокера)"""
    external_device_id: UUID
    metric: str
    value: str
    recorded_at: datetime


class IngestTelemetryRequest(BaseModel):
    """Запрос на прием телеметрии (REST endpoint для симуляции)"""
    deviceId: UUID = Field(..., description="ID устройства")
    metric: str = Field(..., description="Название метрики", example="temperature")
    value: str = Field(..., description="Значение метрики", example="22.5")
    recordedAt: Optional[datetime] = Field(default_factory=datetime.utcnow)


class DeviceStateUpdatedEvent(BaseModel):
    """Событие обновления состояния устройства"""
    external_device_id: UUID
    state: dict
    updated_at: datetime
    source: str = "telemetry"
    last_seen_at: Optional[datetime] = None


# ========== Database Dependency ==========

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ========== In-Memory Storage для событий (для MVP) ==========

telemetry_events: List[TelemetryRecordedEvent] = []
state_events: List[DeviceStateUpdatedEvent] = []


# ========== Helper Functions ==========

async def publish_device_state_event(event: DeviceStateUpdatedEvent):
    """
    Публикация события device.state.updated в брокер
    В реальной реализации здесь будет Kafka producer
    Device Registry подписывается на это событие и обновляет себя
    """
    # Симуляция отправки в Kafka топик 'device.state.updated'
    state_events.append(event)
    print(f"[BROKER] Published event to 'device.state.updated': device={event.external_device_id}, state={event.state}")


async def process_telemetry_event(event: TelemetryRecordedEvent, db: Session):
    """
    Обработка события телеметрии:
    1. Сохранение в Telemetry Store (напрямую в БД)
    2. Формирование и публикация события device.state.updated в брокер
    
    Device Registry самостоятельно подписывается на событие и обновляет состояние
    """
    # 1. Сохранение телеметрии напрямую в БД
    telemetry = TelemetryDataDB(
        external_device_id=event.external_device_id,
        metric=event.metric,
        value=event.value,
        recorded_at=event.recorded_at
    )
    
    db.add(telemetry)
    db.commit()
    
    print(f"[INGEST] Telemetry saved: {event.metric}={event.value} for device {event.external_device_id}")
    
    # 2. Формирование обновленного состояния устройства
    # Логика: последнее значение метрики становится частью state
    device_state = {
        event.metric: event.value
    }
    
    # 3. Публикация события device.state.updated в брокер
    # Device Registry подпишется на это событие и обновит себя
    state_event = DeviceStateUpdatedEvent(
        external_device_id=event.external_device_id,
        state=device_state,
        updated_at=event.recorded_at,
        source="telemetry",
        last_seen_at=datetime.utcnow()
    )
    
    await publish_device_state_event(state_event)


# ========== API Endpoints ==========

@app.get("/health")
async def health_check():
    """Проверка здоровья сервиса"""
    return {"status": "healthy", "service": "telemetry-ingest"}


@app.post("/api/v1/telemetry/ingest", status_code=status.HTTP_202_ACCEPTED)
async def ingest_telemetry(
    request: IngestTelemetryRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    REST endpoint для приема телеметрии (упрощенная версия для отладки)
    В реальной системе телеметрия приходит через брокер сообщений (Kafka)
    """
    # Создание события телеметрии
    event = TelemetryRecordedEvent(
        external_device_id=request.deviceId,
        metric=request.metric,
        value=request.value,
        recorded_at=request.recordedAt
    )
    
    telemetry_events.append(event)
    
    # Асинхронная обработка события
    background_tasks.add_task(process_telemetry_event, event, db)
    
    return {
        "status": "accepted",
        "deviceId": str(request.deviceId),
        "metric": request.metric
    }


@app.get("/internal/telemetry-events")
async def get_telemetry_events():
    """
    Внутренний endpoint для просмотра событий телеметрии (только для отладки MVP)
    """
    return {
        "total_events": len(telemetry_events),
        "events": [
            {
                "device_id": str(event.external_device_id),
                "metric": event.metric,
                "value": event.value,
                "recorded_at": event.recorded_at.isoformat()
            }
            for event in telemetry_events[-100:]  # Последние 100 событий
        ]
    }


@app.get("/internal/state-events")
async def get_state_events():
    """
    Внутренний endpoint для просмотра событий обновления состояния (только для отладки MVP)
    Эти события публикуются в брокер для Device Registry
    """
    return {
        "total_events": len(state_events),
        "events": [
            {
                "device_id": str(event.external_device_id),
                "state": event.state,
                "updated_at": event.updated_at.isoformat(),
                "source": event.source
            }
            for event in state_events[-100:]  # Последние 100 событий
        ]
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003)
