"""
API Gateway
Единая точка входа для всех микросервисов WarmHome
"""
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import httpx
import os

app = FastAPI(
    title="WarmHome API Gateway",
    version="1.0.0",
    description="Единая точка входа для микросервисов WarmHome"
)

# ========== Configuration ==========
DEVICE_REGISTRY_URL = os.getenv("DEVICE_REGISTRY_URL", "http://device-registry:8001")
COMMAND_SERVICE_URL = os.getenv("COMMAND_SERVICE_URL", "http://command-service:8002")
TELEMETRY_INGEST_URL = os.getenv("TELEMETRY_INGEST_URL", "http://telemetry-ingest:8003")
TELEMETRY_QUERY_URL = os.getenv("TELEMETRY_QUERY_URL", "http://telemetry-query:8004")

# HTTP client с timeout
http_client = httpx.AsyncClient(timeout=30.0)


# ========== Helper Functions ==========

async def proxy_request(
    target_url: str,
    method: str,
    path: str = "",
    query_params: dict = None,
    body: bytes = None,
    headers: dict = None
):
    """Проксирование запроса к целевому микросервису"""
    url = f"{target_url}{path}"
    
    try:
        response = await http_client.request(
            method=method,
            url=url,
            params=query_params,
            content=body,
            headers=headers
        )
        
        return JSONResponse(
            content=response.json() if response.text else {},
            status_code=response.status_code
        )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "SERVICE_UNAVAILABLE",
                "message": f"Микросервис недоступен: {str(e)}"
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "code": "INTERNAL_ERROR",
                "message": f"Ошибка шлюза: {str(e)}"
            }
        )


# ========== Health Check ==========

@app.get("/health")
async def health_check():
    """Проверка здоровья API Gateway и всех микросервисов"""
    services_health = {}
    
    services = {
        "device-registry": f"{DEVICE_REGISTRY_URL}/health",
        "command-service": f"{COMMAND_SERVICE_URL}/health",
        "telemetry-ingest": f"{TELEMETRY_INGEST_URL}/health",
        "telemetry-query": f"{TELEMETRY_QUERY_URL}/health"
    }
    
    for service_name, health_url in services.items():
        try:
            response = await http_client.get(health_url, timeout=5.0)
            services_health[service_name] = "healthy" if response.status_code == 200 else "unhealthy"
        except:
            services_health[service_name] = "unreachable"
    
    all_healthy = all(status == "healthy" for status in services_health.values())
    
    return {
        "status": "healthy" if all_healthy else "degraded",
        "service": "api-gateway",
        "services": services_health
    }


# ========== Device Registry Routes ==========

@app.get("/api/v1/device-models")
async def get_device_models(request: Request):
    """Получение каталога моделей устройств"""
    return await proxy_request(
        DEVICE_REGISTRY_URL,
        "GET",
        "/api/v1/device-models",
        query_params=dict(request.query_params)
    )


@app.post("/api/v1/devices")
async def create_device(request: Request):
    """Регистрация нового устройства"""
    body = await request.body()
    return await proxy_request(
        DEVICE_REGISTRY_URL,
        "POST",
        "/api/v1/devices",
        body=body,
        headers={"Content-Type": "application/json"}
    )


@app.get("/api/v1/devices")
async def list_devices(request: Request):
    """Получение списка устройств"""
    return await proxy_request(
        DEVICE_REGISTRY_URL,
        "GET",
        "/api/v1/devices",
        query_params=dict(request.query_params)
    )


@app.get("/api/v1/devices/{device_id}")
async def get_device(device_id: str, request: Request):
    """Получение информации об устройстве"""
    return await proxy_request(
        DEVICE_REGISTRY_URL,
        "GET",
        f"/api/v1/devices/{device_id}"
    )


@app.get("/api/v1/devices/{device_id}/state")
async def get_device_state(device_id: str, request: Request):
    """Получение состояния устройства"""
    return await proxy_request(
        DEVICE_REGISTRY_URL,
        "GET",
        f"/api/v1/devices/{device_id}/state"
    )


# ========== Command Service Routes ==========

@app.post("/api/v1/devices/{device_id}/commands")
async def create_command(device_id: str, request: Request):
    """Отправка команды устройству"""
    body = await request.body()
    return await proxy_request(
        COMMAND_SERVICE_URL,
        "POST",
        f"/api/v1/devices/{device_id}/commands",
        body=body,
        headers={"Content-Type": "application/json"}
    )


@app.get("/api/v1/commands/{command_id}")
async def get_command(command_id: str, request: Request):
    """Получение статуса команды"""
    return await proxy_request(
        COMMAND_SERVICE_URL,
        "GET",
        f"/api/v1/commands/{command_id}"
    )


@app.get("/api/v1/devices/{device_id}/commands")
async def list_device_commands(device_id: str, request: Request):
    """Получение списка команд для устройства"""
    return await proxy_request(
        COMMAND_SERVICE_URL,
        "GET",
        f"/api/v1/devices/{device_id}/commands",
        query_params=dict(request.query_params)
    )


# ========== Telemetry Routes ==========

@app.post("/api/v1/telemetry/ingest")
async def ingest_telemetry(request: Request):
    """Прием телеметрии от устройства"""
    body = await request.body()
    return await proxy_request(
        TELEMETRY_INGEST_URL,
        "POST",
        "/api/v1/telemetry/ingest",
        body=body,
        headers={"Content-Type": "application/json"}
    )


@app.get("/api/v1/devices/{device_id}/telemetry")
async def get_device_telemetry(device_id: str, request: Request):
    """Получение телеметрии устройства"""
    return await proxy_request(
        TELEMETRY_QUERY_URL,
        "GET",
        f"/api/v1/devices/{device_id}/telemetry",
        query_params=dict(request.query_params)
    )


@app.get("/api/v1/devices/{device_id}/telemetry/latest")
async def get_latest_telemetry(device_id: str, request: Request):
    """Получение последнего значения телеметрии"""
    return await proxy_request(
        TELEMETRY_QUERY_URL,
        "GET",
        f"/api/v1/devices/{device_id}/telemetry/latest",
        query_params=dict(request.query_params)
    )


@app.get("/api/v1/telemetry")
async def get_all_telemetry(request: Request):
    """Получение телеметрии всех устройств"""
    return await proxy_request(
        TELEMETRY_QUERY_URL,
        "GET",
        "/api/v1/telemetry",
        query_params=dict(request.query_params)
    )


# ========== Shutdown ==========

@app.on_event("shutdown")
async def shutdown_event():
    """Закрытие HTTP клиента при завершении"""
    await http_client.aclose()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
