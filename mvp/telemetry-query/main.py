"""
Telemetry Query Service
Микросервис для чтения телеметрии и истории измерений
"""
from fastapi import FastAPI, HTTPException, status, Query as QueryParam, Depends
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID, uuid4
import uvicorn
import os
from sqlalchemy import create_engine, Column, String, DateTime, desc
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.dialects.postgresql import UUID as PGUUID

# ========== Database Configuration ==========
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://warmhouse:warmhouse@telemetry-db:5432/telemetry_store")

engine = create_engine(DATABASE_URL)
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

app = FastAPI(title="Telemetry Query Service", version="1.0.0")


# ========== Pydantic Models ==========

class TelemetryData(BaseModel):
    """Данные телеметрии"""
    id: UUID
    externalDeviceId: UUID
    metric: str
    value: str
    recordedAt: datetime
    
    class Config:
        from_attributes = True


class CreateTelemetryRequest(BaseModel):
    """Внутренний запрос на создание записи телеметрии"""
    externalDeviceId: UUID
    metric: str
    value: str
    recordedAt: datetime


class TelemetryResponse(BaseModel):
    """Ответ со списком телеметрии"""
    items: List[TelemetryData]


# ========== Database Dependency ==========

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ========== API Endpoints ==========

@app.get("/health")
async def health_check():
    """Проверка здоровья сервиса"""
    return {"status": "healthy", "service": "telemetry-query"}


@app.get("/api/v1/devices/{device_id}/telemetry", response_model=TelemetryResponse)
async def get_device_telemetry(
    device_id: UUID,
    metric: Optional[str] = QueryParam(None, description="Фильтр по метрике"),
    from_date: Optional[datetime] = QueryParam(None, alias="from", description="Начало периода"),
    to_date: Optional[datetime] = QueryParam(None, alias="to", description="Конец периода"),
    limit: int = QueryParam(100, ge=1, le=500, description="Количество записей"),
    offset: int = QueryParam(0, ge=0, description="Смещение для пагинации"),
    db: Session = Depends(get_db)
):
    """
    Получение телеметрии устройства
    Возвращает временной ряд измерений с возможностью фильтрации
    """
    query = db.query(TelemetryDataDB).filter(
        TelemetryDataDB.external_device_id == device_id
    )
    
    if metric:
        query = query.filter(TelemetryDataDB.metric == metric)
    
    if from_date:
        query = query.filter(TelemetryDataDB.recorded_at >= from_date)
    
    if to_date:
        query = query.filter(TelemetryDataDB.recorded_at <= to_date)
    
    # Сортировка по времени (новые первыми)
    query = query.order_by(desc(TelemetryDataDB.recorded_at))
    
    # Пагинация
    items_db = query.offset(offset).limit(limit).all()
    
    items = [
        TelemetryData(
            id=item.id,
            externalDeviceId=item.external_device_id,
            metric=item.metric,
            value=item.value,
            recordedAt=item.recorded_at
        )
        for item in items_db
    ]
    
    return TelemetryResponse(items=items)


@app.get("/api/v1/devices/{device_id}/telemetry/latest")
async def get_latest_telemetry(
    device_id: UUID,
    metric: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Получение последних значений телеметрии устройства"""
    query = db.query(TelemetryDataDB).filter(
        TelemetryDataDB.external_device_id == device_id
    )
    
    if metric:
        query = query.filter(TelemetryDataDB.metric == metric)
    
    item = query.order_by(desc(TelemetryDataDB.recorded_at)).first()
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "NOT_FOUND",
                "message": "Telemetry data not found",
                "details": {"resource": "telemetry", "deviceId": str(device_id)}
            }
        )
    
    return TelemetryData(
        id=item.id,
        externalDeviceId=item.external_device_id,
        metric=item.metric,
        value=item.value,
        recordedAt=item.recorded_at
    )


@app.get("/api/v1/telemetry", response_model=TelemetryResponse)
async def get_all_telemetry(
    metric: Optional[str] = QueryParam(None, description="Фильтр по метрике"),
    from_date: Optional[datetime] = QueryParam(None, alias="from", description="Начало периода"),
    to_date: Optional[datetime] = QueryParam(None, alias="to", description="Конец периода"),
    limit: int = QueryParam(100, ge=1, le=500, description="Количество записей"),
    offset: int = QueryParam(0, ge=0, description="Смещение для пагинации"),
    db: Session = Depends(get_db)
):
    """Получение телеметрии всех устройств"""
    query = db.query(TelemetryDataDB)
    
    if metric:
        query = query.filter(TelemetryDataDB.metric == metric)
    
    if from_date:
        query = query.filter(TelemetryDataDB.recorded_at >= from_date)
    
    if to_date:
        query = query.filter(TelemetryDataDB.recorded_at <= to_date)
    
    # Сортировка по времени (новые первыми)
    query = query.order_by(desc(TelemetryDataDB.recorded_at))
    
    # Пагинация
    items_db = query.offset(offset).limit(limit).all()
    
    items = [
        TelemetryData(
            id=item.id,
            externalDeviceId=item.external_device_id,
            metric=item.metric,
            value=item.value,
            recordedAt=item.recorded_at
        )
        for item in items_db
    ]
    
    return TelemetryResponse(items=items)


@app.post("/internal/telemetry", status_code=status.HTTP_201_CREATED)
async def create_telemetry(request: CreateTelemetryRequest, db: Session = Depends(get_db)):
    """
    Внутренний endpoint для записи телеметрии
    Используется Telemetry Ingest Service
    """
    telemetry = TelemetryDataDB(
        external_device_id=request.externalDeviceId,
        metric=request.metric,
        value=request.value,
        recorded_at=request.recordedAt
    )
    
    db.add(telemetry)
    db.commit()
    db.refresh(telemetry)
    
    return {
        "status": "created",
        "id": str(telemetry.id),
        "deviceId": str(telemetry.external_device_id)
    }


@app.get("/internal/stats")
async def get_stats(db: Session = Depends(get_db)):
    """Статистика хранилища телеметрии (для отладки MVP)"""
    from sqlalchemy import func
    
    total_records = db.query(func.count(TelemetryDataDB.id)).scalar()
    
    unique_devices = db.query(
        func.count(func.distinct(TelemetryDataDB.external_device_id))
    ).scalar()
    
    unique_metrics = db.query(
        func.count(func.distinct(TelemetryDataDB.metric))
    ).scalar()
    
    # Подсчет по метрикам
    metrics_breakdown = db.query(
        TelemetryDataDB.metric,
        func.count(TelemetryDataDB.id)
    ).group_by(TelemetryDataDB.metric).all()
    
    metrics_count = {metric: count for metric, count in metrics_breakdown}
    
    # Временные границы
    oldest = db.query(func.min(TelemetryDataDB.recorded_at)).scalar()
    latest = db.query(func.max(TelemetryDataDB.recorded_at)).scalar()
    
    return {
        "total_records": total_records,
        "unique_devices": unique_devices,
        "unique_metrics": unique_metrics,
        "metrics_breakdown": metrics_count,
        "oldest_record": oldest,
        "latest_record": latest
    }


@app.delete("/internal/telemetry", status_code=status.HTTP_204_NO_CONTENT)
async def clear_telemetry(db: Session = Depends(get_db)):
    """Очистка хранилища телеметрии (для тестирования MVP)"""
    db.query(TelemetryDataDB).delete()
    db.commit()
    return None


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8004)
