"""
Command Service
Микросервис для управления командами устройствами в системе WarmHome
"""
from fastapi import FastAPI, HTTPException, status, Depends
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID, uuid4
import uvicorn
import asyncio
import os
from sqlalchemy import create_engine, Column, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.dialects.postgresql import UUID as PGUUID

# ========== Database Configuration ==========
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://warmhouse:warmhouse@command-db:5432/command_service")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ========== Database Models ==========

class CommandDB(Base):
    __tablename__ = "commands"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    external_device_id = Column(PGUUID(as_uuid=True), nullable=False)
    command_type = Column(String, nullable=False)
    payload = Column(Text, nullable=True)  # JSON string
    status = Column(String, default="pending")  # pending|succeeded|failed
    created_at = Column(DateTime, nullable=False)


# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Command Service", version="1.0.0")


# ========== Pydantic Models ==========

class CreateCommandRequest(BaseModel):
    """Запрос на создание команды"""
    commandType: str = Field(..., description="Тип команды", example="HEAT_RELAY_SET")
    payload: Optional[dict] = Field(None, description="Параметры команды")


class Command(BaseModel):
    """Команда управления устройством"""
    id: UUID
    externalDeviceId: UUID
    commandType: str
    payload: Optional[dict] = None
    status: str
    createdAt: datetime
    
    class Config:
        from_attributes = True


class CommandCreatedEvent(BaseModel):
    """Событие о создании команды (публикуется в брокер)"""
    id: UUID
    external_device_id: UUID
    command_type: str
    payload: Optional[dict] = None
    created_at: datetime


# ========== Database Dependency ==========

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ========== Message Broker Simulation ==========

async def publish_command_event(event: CommandCreatedEvent):
    """
    Публикация события о создании команды в брокер
    В реальной реализации здесь будет Kafka producer
    """
    # Симуляция отправки в Kafka топик 'command.created'
    print(f"[BROKER] Published event to 'command.created': {event.id}")
    
    # Симуляция асинхронной обработки команды
    asyncio.create_task(simulate_command_execution(event.id))


async def simulate_command_execution(command_id: UUID):
    """
    Симуляция выполнения команды (в реальной системе делает Protocol Adapter)
    """
    await asyncio.sleep(2)  # Симуляция времени выполнения
    
    db = SessionLocal()
    try:
        command = db.query(CommandDB).filter(CommandDB.id == command_id).first()
        if command:
            command.status = "succeeded"
            db.commit()
            print(f"[ADAPTER] Command {command_id} executed successfully")
    finally:
        db.close()


# ========== API Endpoints ==========

@app.get("/health")
async def health_check():
    """Проверка здоровья сервиса"""
    return {"status": "healthy", "service": "command-service"}


@app.post("/api/v1/devices/{device_id}/commands", 
          response_model=Command, 
          status_code=status.HTTP_202_ACCEPTED)
async def create_command(
    device_id: UUID,
    request: CreateCommandRequest,
    db: Session = Depends(get_db)
):
    """
    Отправка команды устройству
    Команда принимается к обработке и асинхронно доставляется через адаптеры
    """
    import json
    
    # Создание команды
    command_db = CommandDB(
        external_device_id=device_id,
        command_type=request.commandType,
        payload=json.dumps(request.payload) if request.payload else None,
        status="pending",
        created_at=datetime.utcnow()
    )
    
    db.add(command_db)
    db.commit()
    db.refresh(command_db)
    
    # Публикация события в брокер
    event = CommandCreatedEvent(
        id=command_db.id,
        external_device_id=device_id,
        command_type=command_db.command_type,
        payload=request.payload,
        created_at=command_db.created_at
    )
    
    await publish_command_event(event)
    
    return Command(
        id=command_db.id,
        externalDeviceId=command_db.external_device_id,
        commandType=command_db.command_type,
        payload=json.loads(command_db.payload) if command_db.payload else None,
        status=command_db.status,
        createdAt=command_db.created_at
    )


@app.get("/api/v1/commands/{command_id}", response_model=Command)
async def get_command(command_id: UUID, db: Session = Depends(get_db)):
    """Получение информации о команде"""
    import json
    
    command = db.query(CommandDB).filter(CommandDB.id == command_id).first()
    
    if not command:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "NOT_FOUND",
                "message": "Command not found",
                "details": {"resource": "command", "id": str(command_id)}
            }
        )
    
    return Command(
        id=command.id,
        externalDeviceId=command.external_device_id,
        commandType=command.command_type,
        payload=json.loads(command.payload) if command.payload else None,
        status=command.status,
        createdAt=command.created_at
    )


@app.get("/api/v1/devices/{device_id}/commands", response_model=List[Command])
async def list_device_commands(
    device_id: UUID,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Получение списка команд для устройства"""
    import json
    
    commands = db.query(CommandDB).filter(
        CommandDB.external_device_id == device_id
    ).order_by(CommandDB.created_at.desc()).limit(limit).all()
    
    return [
        Command(
            id=cmd.id,
            externalDeviceId=cmd.external_device_id,
            commandType=cmd.command_type,
            payload=json.loads(cmd.payload) if cmd.payload else None,
            status=cmd.status,
            createdAt=cmd.created_at
        )
        for cmd in commands
    ]


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
