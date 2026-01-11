## Допущения

В рамках данного задания процессы аутентификации и авторизации пользователей не детализируются.
Предполагается, что пользователь и администратор уже аутентифицированы, а механизмы управления доступами находятся вне рассматриваемой архитектурной модели.


```puml
@startuml
!includeurl https://raw.githubusercontent.com/RicardoNiepel/C4-PlantUML/master/C4_Container.puml

LAYOUT_WITH_LEGEND()
top to bottom direction

skinparam defaultFontSize 9
skinparam wrapWidth 160
skinparam Padding 2
skinparam NodePadding 2
skinparam ArrowThickness 0.7

title Тёплый дом — целевая архитектура (To-Be), уровень контейнеров

Person(user, "Пользователь", "Управляет устройствами и просматривает телеметрию")
Person(admin, "Администратор", "Загружает и обновляет партнёров и модели устройств")

System_Boundary(warmHome, "Экосистема «Тёплый дом» (SaaS)") {

  ' ===== UI layer =====
  Container(webApp, "Web UI", "Web Application", "Личный кабинет пользователя")
  Container(adminApp, "Admin UI", "Web Application", "Админ-панель (каталог партнёров/моделей)")

  ' ===== Edge layer =====
  Container(apiGateway, "API Gateway", "Web API", "Единая точка входа")

  ' ===== Core services layer =====
  together {
    Container(identityOwnership, "Identity & Ownership Service", "Service (HTTP)", "Пользователь, дома/зоны, владение и доступы")
    Container(deviceRegistry, "Device Registry", "Service (HTTP)", "Реестр устройств + партнёры и модели устройств")
    Container(telemetryQuery, "Telemetry Query Service", "Service (HTTP)", "Чтение телеметрии")
    Container(rulesEngine, "Rules Service", "Service (HTTP)", "Сценарии автоматизации")
    Container(commandSvc, "Command Service", "Service (HTTP + Async)", "Команды управления")

    ContainerDb(identityOwnershipDb, "Identity & Ownership DB", "Database", "Пользователи, дома, зоны, владение и права доступа")
    ContainerDb(registryDb, "Device Registry DB", "Database", "Устройства, партнёры, модели и capabilities")
    ContainerDb(rulesDb, "Rules DB", "Database", "Пользовательские сценарии и правила автоматизации")
  }

  ' ===== Data layer =====
  ContainerDb(commandDb, "Command DB", "Database", "Команды управления")
  ContainerDb(telemetryStore, "Telemetry Store", "Time-series storage", "Телеметрия")

  ' ===== Async layer =====
  ContainerQueue(eventBus, "Message Broker", "Kafka", "Команды и события")

  ' ===== Integration layer =====
  Container(adapters, "Protocol Adapter Service", "Service (Async + REST)", "Адаптеры протоколов устройств")

  ' ===== Telemetry ingest =====
  Container(telemetryIngest, "Telemetry Ingest Service", "Service (Async)", "Приём и нормализация телеметрии")
}

System_Ext(sensorApi, "Home Devices API", "Внешняя система взаимодействия с устройствами")

' ===== User flow =====
Rel_D(user, webApp, "Использует интерфейс", "HTTPS")
Rel_D(webApp, apiGateway, "Вызывает backend API", "HTTPS/REST")

' ===== Admin flow =====
Rel_D(admin, adminApp, "Использует админ-панель", "HTTPS")
Rel_D(adminApp, apiGateway, "Вызывает административные API", "HTTPS/REST")

' ===== Sync (UI -> core) =====
Rel_D(apiGateway, identityOwnership, "Управление пользователем, домами и доступами", "HTTPS/REST")
Rel_D(apiGateway, deviceRegistry, "Управление устройствами, партнёрами и моделями", "HTTPS/REST")
Rel_D(apiGateway, commandSvc, "Отправка команд управления", "HTTPS/REST")
Rel_D(apiGateway, telemetryQuery, "Запрос телеметрии", "HTTPS/REST")
Rel_D(apiGateway, rulesEngine, "Управление сценариями автоматизации", "HTTPS/REST")

' ===== Sync (Rules -> Command) =====
Rel_D(rulesEngine, commandSvc, "Запуск команд по сценариям", "HTTPS/REST")

' ===== DB =====
Rel_D(identityOwnership, identityOwnershipDb, "Чтение и запись данных")
Rel_D(deviceRegistry, registryDb, "Чтение и запись данных")
Rel_D(commandSvc, commandDb, "Чтение и запись команд")
Rel_D(telemetryIngest, telemetryStore, "Запись телеметрии")
Rel_D(telemetryQuery, telemetryStore, "Чтение телеметрии")
Rel_D(rulesEngine, rulesDb, "Чтение и запись сценариев")


' ===== Async (device integration & telemetry) =====
Rel_D(commandSvc, eventBus, "Публикация команд управления", "Async")
Rel_D(eventBus, adapters, "Доставка команд устройствам", "Async")
Rel_U(adapters, eventBus, "Публикация телеметрии и статусов устройств", "Async")
Rel_D(eventBus, telemetryIngest, "Доставка телеметрии", "Async")
Rel_D(eventBus, deviceRegistry, "События состояния и доступности устройств", "Async")

' ===== External =====
Rel_D(adapters, sensorApi, "Вызовы внешнего API устройств", "REST API")
@enduml
```