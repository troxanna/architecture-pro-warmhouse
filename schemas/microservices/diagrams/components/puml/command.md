```puml
@startuml
!includeurl https://raw.githubusercontent.com/RicardoNiepel/C4-PlantUML/master/C4_Component.puml
title Command Service — верхнеуровневая диаграмма компонентов

ContainerDb_Ext(commandDb, "Command DB", "Database", "Команды и статусы")
ContainerQueue_Ext(eventBus, "Message Broker", "Kafka", "Команды/статусы")

Container_Boundary(cs, "Command Service") {
  Component(api, "API слой", "FastAPI Controllers", "HTTP endpoint отправки команд")
  Component(useCases, "Use Cases", "Application layer", "Сценарий: принять команду, проверить, сохранить статус")
  Component(domain, "Domain Model", "Domain layer", "Command, CommandStatus, инварианты")
  Component(repo, "Repository", "Infrastructure", "Команды/статусы в БД")
  Component(publisher, "Command Publisher", "Infrastructure", "Публикация команд в брокер")
}

Rel(api, useCases, "Вызывает")
Rel(useCases, domain, "Использует")
Rel(useCases, repo, "Читает/пишет через")
Rel(repo, commandDb, "CRUD", "SQL")
Rel(useCases, publisher, "Публикует команду")
Rel(publisher, eventBus, "Publish command", "Async")

@enduml
```