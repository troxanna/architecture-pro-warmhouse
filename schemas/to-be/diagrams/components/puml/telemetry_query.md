```puml
@startuml
!includeurl https://raw.githubusercontent.com/RicardoNiepel/C4-PlantUML/master/C4_Component.puml
title Telemetry Query Service — верхнеуровневая диаграмма компонентов

ContainerDb_Ext(telemetryStore, "Telemetry Store", "Time-series storage", "История телеметрии")

Container_Boundary(tq, "Telemetry Query Service") {
  Component(api, "API слой", "FastAPI Controllers", "HTTP endpoints: latest/history")
  Component(useCases, "Use Cases", "Application layer", "Сценарии чтения и подготовки ответа")
  Component(domain, "Query Model", "Domain/Model", "TelemetryPoint, TimeRange, фильтры")
  Component(repo, "Read Repository", "Infrastructure", "Чтение из TS storage")
}

Rel(api, useCases, "Вызывает")
Rel(useCases, domain, "Использует")
Rel(useCases, repo, "Читает через")
Rel(repo, telemetryStore, "Read", "TS read")

@enduml
```