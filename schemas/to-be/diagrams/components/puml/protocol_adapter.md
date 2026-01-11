```puml
@startuml
!includeurl https://raw.githubusercontent.com/RicardoNiepel/C4-PlantUML/master/C4_Component.puml
title Protocol Adapter Service — верхнеуровневая диаграмма компонентов

ContainerQueue_Ext(eventBus, "Message Broker", "Kafka", "Команды/телеметрия")
System_Ext(sensorApi, "Home Devices API", "Внешняя система устройств")

Container_Boundary(pa, "Protocol Adapter Service") {
  Component(cmdConsumer, "Command Consumer", "Infrastructure", "Читает команды из брокера")
  Component(dispatcher, "Dispatcher", "Infrastructure", "Выбор протокольного адаптера по типу устройства")
  Component(protocolClient, "Protocol Client", "Infrastructure", "Вызовы к Home Devices API (httpx/requests)")
  Component(telemetryMapper, "Telemetry Mapper", "Infrastructure", "Преобразование статусов/телеметрии во внутренний формат событий")
  Component(publisher, "Telemetry/Status Publisher", "Infrastructure", "Публикация телеметрии/статусов в брокер")
}

Rel(cmdConsumer, eventBus, "Consume command", "Async")
Rel(cmdConsumer, dispatcher, "Передаёт команду")
Rel(dispatcher, protocolClient, "Доставка")
Rel(protocolClient, sensorApi, "Device calls", "REST API")
Rel(protocolClient, telemetryMapper, "Возвращает статусы/данные")
Rel(telemetryMapper, publisher, "Формирует события")
Rel(publisher, eventBus, "Publish telemetry/status", "Async")

@enduml
```