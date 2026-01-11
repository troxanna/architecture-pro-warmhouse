```puml
@startuml
!includeurl https://raw.githubusercontent.com/RicardoNiepel/C4-PlantUML/master/C4_Component.puml
title Rules Service — верхнеуровневая диаграмма компонентов

Container_Ext(commandSvc, "Command Service", "HTTP API", "Приём команд управления")
ContainerDb_Ext(rulesDb, "Rules DB", "Database", "Правила и сценарии (логическое хранилище)")

Container_Boundary(rs, "Rules Service") {
  Component(api, "API слой", "FastAPI Controllers", "CRUD сценариев пользователя")
  Component(useCases, "Use Cases", "Application layer", "Сценарии: create/update/enable сценарии")
  Component(domain, "Domain Model", "Domain layer", "Rule, Trigger, Condition, Action")
  Component(cmdClient, "Command Service Client", "Infrastructure", "HTTP-клиент для отправки команд в Command Service")
  Component(repo, "Repository", "Infrastructure", "Хранение и чтение правил")
  Component(scheduler, "Scheduler Adapter", "Infrastructure", "Триггер выполнения по времени")

}

Rel(api, useCases, "Вызывает")

Rel(useCases, domain, "Использует")
Rel(useCases, repo, "Читает/пишет через")
Rel(repo, rulesDb, "CRUD", "SQL")
Rel(scheduler, useCases, "Триггерит выполнение")

Rel(useCases, cmdClient, "Инициирует выполнение команд")
Rel(cmdClient, commandSvc, "HTTPS/REST")

@enduml
```
