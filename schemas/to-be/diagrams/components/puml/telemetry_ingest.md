```puml
@startuml
!includeurl https://raw.githubusercontent.com/RicardoNiepel/C4-PlantUML/master/C4_Component.puml
title Telemetry Ingest Service — верхнеуровневая диаграмма компонентов

ContainerQueue_Ext(eventBus, "Message Broker", "Kafka", "События телеметрии")
ContainerDb_Ext(telemetryStore, "Telemetry Store", "Time-series storage", "История телеметрии")

Container_Boundary(ti, "Telemetry Ingest Service") {
  Component(consumer, "Message Consumer", "aiokafka", "Читает события телеметрии из брокера")
  Component(processing, "Processing Pipeline", "Application layer", "Валидация/нормализация/обогащение")
  Component(model, "Ingest Model", "Model", "TelemetryEvent, метрики, теги")
  Component(writer, "Write Repository", "Infrastructure", "Запись в TS storage")
}

Rel(consumer, eventBus, "Consume", "Async")
Rel(consumer, processing, "Передаёт события")
Rel(processing, model, "Формирует/использует")
Rel(processing, writer, "Записывает через")
Rel(writer, telemetryStore, "Write", "TS write")

@enduml
```