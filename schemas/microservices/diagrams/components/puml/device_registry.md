```puml
@startuml
!includeurl https://raw.githubusercontent.com/RicardoNiepel/C4-PlantUML/master/C4_Component.puml
title Device Registry — верхнеуровневая диаграмма компонентов

ContainerDb_Ext(registryDb, "Device Registry DB", "Database", "Устройства, онбординг, привязка к дому/зоне")

Container_Boundary(reg, "Device Registry") {
  Component(api, "API слой", "FastAPI Controllers", "HTTP endpoints для регистрации/привязки/чтения устройств")
  Component(useCases, "Use Cases", "Application layer", " Сценарии: register/bind/list/update/delete")
  Component(domain, "Domain Model", "Domain layer", "Агрегаты и правила: Device, OnboardingStatus, инварианты")
  Component(repo, "Repository", "Infrastructure", "Доступ к БД")
}


Rel(api, useCases, "Вызывает")
Rel(useCases, domain, "Использует")
Rel(useCases, repo, "Читает/пишет через")
Rel(repo, registryDb, "CRUD", "SQL")
@enduml
```