"""
Device Registry Service
Микросервис для управления устройствами в системе WarmHome
"""
from fastapi import FastAPI, HTTPException, status, Depends
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID, uuid4
import uvicorn
import os
from sqlalchemy import create_engine, Column, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.dialects.postgresql import UUID as PGUUID

# ========== Database Configuration ==========
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://warmhouse:warmhouse@registry-db:5432/device_registry")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ========== Database Models ==========

class DeviceModelDB(Base):
    __tablename__ = "device_models"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String, nullable=False)
    device_type = Column(String, nullable=False)
    protocol = Column(String, nullable=False)


class DeviceDB(Base):
    __tablename__ = "devices"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    device_model_id = Column(PGUUID(as_uuid=True), nullable=False)
    serial_number = Column(String, unique=True, nullable=False)
    display_name = Column(String, nullable=False)
    external_house_id = Column(PGUUID(as_uuid=True), nullable=False)
    external_zone_id = Column(PGUUID(as_uuid=True), nullable=True)
    installed_at = Column(DateTime, nullable=True)
    status = Column(String, default="offline")
    lifecycle_state = Column(String, default="provisioning")
    last_seen_at = Column(DateTime, nullable=True)


class DeviceStateDB(Base):
    __tablename__ = "device_states"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    device_id = Column(PGUUID(as_uuid=True), unique=True, nullable=False)
    state = Column(String, nullable=False)  # JSON string
    updated_at = Column(DateTime, nullable=False)
    source = Column(String, nullable=False)


# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Device Registry Service", version="1.0.0")


# ========== Pydantic Models ==========

class DeviceModel(BaseModel):
    """Модель устройства"""
    id: UUID
    name: str
    device_type: str
    protocol: str
    
    class Config:
        from_attributes = True


class CreateDeviceRequest(BaseModel):
    """Запрос на создание устройства"""
    deviceModelId: UUID = Field(..., description="ID модели устройства")
    serialNumber: str = Field(..., description="Серийный номер")
    displayName: str = Field(..., description="Отображаемое имя")
    externalHouseId: UUID = Field(..., description="ID дома из Identity Service")
    externalZoneId: Optional[UUID] = Field(None, description="ID зоны из Identity Service")


class Device(BaseModel):
    """Устройство"""
    id: UUID
    deviceModelId: UUID
    serialNumber: str
    displayName: str
    externalHouseId: UUID
    externalZoneId: Optional[UUID] = None
    installedAt: Optional[datetime] = None
    status: str
    lifecycleState: str
    lastSeenAt: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class DeviceState(BaseModel):
    """Состояние устройства"""
    id: UUID
    deviceId: UUID
    state: dict
    updatedAt: datetime
    source: str
    
    class Config:
        from_attributes = True


# ========== Database Dependency ==========

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ========== Initialization ==========

def init_device_models(db: Session):
    """Инициализация предустановленных моделей устройств"""
    if db.query(DeviceModelDB).count() == 0:
        models = [
            DeviceModelDB(
                id=UUID("7d7c8e0b-8f41-4f3c-9d9c-0f2b3b2c1d10"),
                name="Temperature Sensor Model A",
                device_type="temperature_sensor",
                protocol="http"
            ),
            DeviceModelDB(
                id=UUID("8e8d9f1c-9f52-4f4d-9e9d-1f3c4c3d2e21"),
                name="Heat Relay Model B",
                device_type="relay",
                protocol="http"
            )
        ]
        db.add_all(models)
        db.commit()


@app.on_event("startup")
async def startup_event():
    """Инициализация при запуске"""
    db = SessionLocal()
    try:
        init_device_models(db)
    finally:
        db.close()


# ========== API Endpoints ==========

@app.get("/health")
async def health_check():
    """Проверка здоровья сервиса"""
    return {"status": "healthy", "service": "device-registry"}


@app.post("/api/v1/devices", response_model=Device, status_code=status.HTTP_201_CREATED)
async def create_device(request: CreateDeviceRequest, db: Session = Depends(get_db)):
    """Регистрация нового устройства"""
    # Проверка существования модели устройства
    device_model = db.query(DeviceModelDB).filter(
        DeviceModelDB.id == request.deviceModelId
    ).first()
    
    if not device_model:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "VALIDATION_ERROR",
                "message": "Device model not found",
                "details": {"field": "deviceModelId", "reason": "invalid"}
            }
        )
    
    # Проверка уникальности серийного номера
    existing = db.query(DeviceDB).filter(
        DeviceDB.serial_number == request.serialNumber
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "CONFLICT",
                "message": "Device already exists",
                "details": {"field": "serialNumber", "value": request.serialNumber}
            }
        )
    
    # Создание устройства
    device_db = DeviceDB(
        device_model_id=request.deviceModelId,
        serial_number=request.serialNumber,
        display_name=request.displayName,
        external_house_id=request.externalHouseId,
        external_zone_id=request.externalZoneId,
        installed_at=datetime.utcnow(),
        status="offline",
        lifecycle_state="provisioning"
    )
    
    db.add(device_db)
    db.commit()
    db.refresh(device_db)
    
    # Создание начального состояния
    state_db = DeviceStateDB(
        device_id=device_db.id,
        state="{}",
        updated_at=datetime.utcnow(),
        source="telemetry"
    )
    db.add(state_db)
    db.commit()
    
    return Device(
        id=device_db.id,
        deviceModelId=device_db.device_model_id,
        serialNumber=device_db.serial_number,
        displayName=device_db.display_name,
        externalHouseId=device_db.external_house_id,
        externalZoneId=device_db.external_zone_id,
        installedAt=device_db.installed_at,
        status=device_db.status,
        lifecycleState=device_db.lifecycle_state,
        lastSeenAt=device_db.last_seen_at
    )


@app.get("/api/v1/devices/{device_id}", response_model=Device)
async def get_device(device_id: UUID, db: Session = Depends(get_db)):
    """Получение информации об устройстве"""
    device = db.query(DeviceDB).filter(DeviceDB.id == device_id).first()
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "NOT_FOUND",
                "message": "Device not found",
                "details": {"resource": "device", "id": str(device_id)}
            }
        )
    
    return Device(
        id=device.id,
        deviceModelId=device.device_model_id,
        serialNumber=device.serial_number,
        displayName=device.display_name,
        externalHouseId=device.external_house_id,
        externalZoneId=device.external_zone_id,
        installedAt=device.installed_at,
        status=device.status,
        lifecycleState=device.lifecycle_state,
        lastSeenAt=device.last_seen_at
    )


@app.get("/api/v1/devices", response_model=List[Device])
async def list_devices(
    external_house_id: Optional[UUID] = None,
    db: Session = Depends(get_db)
):
    """Получение списка устройств"""
    query = db.query(DeviceDB)
    
    if external_house_id:
        query = query.filter(DeviceDB.external_house_id == external_house_id)
    
    devices = query.all()
    
    return [
        Device(
            id=d.id,
            deviceModelId=d.device_model_id,
            serialNumber=d.serial_number,
            displayName=d.display_name,
            externalHouseId=d.external_house_id,
            externalZoneId=d.external_zone_id,
            installedAt=d.installed_at,
            status=d.status,
            lifecycleState=d.lifecycle_state,
            lastSeenAt=d.last_seen_at
        )
        for d in devices
    ]


@app.get("/api/v1/devices/{device_id}/state", response_model=DeviceState)
async def get_device_state(device_id: UUID, db: Session = Depends(get_db)):
    """Получение текущего состояния устройства"""
    device = db.query(DeviceDB).filter(DeviceDB.id == device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "NOT_FOUND",
                "message": "Device not found",
                "details": {"resource": "device", "id": str(device_id)}
            }
        )
    
    state = db.query(DeviceStateDB).filter(
        DeviceStateDB.device_id == device_id
    ).first()
    
    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "NOT_FOUND",
                "message": "Device state not found",
                "details": {"resource": "deviceState", "deviceId": str(device_id)}
            }
        )
    
    import json
    return DeviceState(
        id=state.id,
        deviceId=state.device_id,
        state=json.loads(state.state),
        updatedAt=state.updated_at,
        source=state.source
    )


@app.put("/api/v1/devices/{device_id}/state")
async def update_device_state(
    device_id: UUID,
    state: dict,
    source: str = "telemetry",
    db: Session = Depends(get_db)
):
    """Обновление состояния устройства"""
    import json
    
    device = db.query(DeviceDB).filter(DeviceDB.id == device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": "Device not found"}
        )
    
    # Обновление состояния
    state_db = db.query(DeviceStateDB).filter(
        DeviceStateDB.device_id == device_id
    ).first()
    
    if state_db:
        state_db.state = json.dumps(state)
        state_db.updated_at = datetime.utcnow()
        state_db.source = source
    else:
        state_db = DeviceStateDB(
            device_id=device_id,
            state=json.dumps(state),
            updated_at=datetime.utcnow(),
            source=source
        )
        db.add(state_db)
    
    # Обновление устройства
    device.last_seen_at = datetime.utcnow()
    device.status = "online"
    if device.lifecycle_state == "provisioning":
        device.lifecycle_state = "active"
    
    db.commit()
    
    return {"status": "updated", "deviceId": str(device_id)}


@app.get("/api/v1/device-models", response_model=List[DeviceModel])
async def list_device_models(db: Session = Depends(get_db)):
    """Получение каталога моделей устройств"""
    models = db.query(DeviceModelDB).all()
    return [DeviceModel.from_orm(m) for m in models]


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
