```puml
@startuml
!includeurl https://raw.githubusercontent.com/RicardoNiepel/C4-PlantUML/master/C4_Component.puml
title Identity & Ownership Service — верхнеуровневая диаграмма компонентов

ContainerDb_Ext(userDb, "Identity & Ownership  DB", "Database", "Профили пользователей")

Container_Boundary(profile, "Identity & Ownership Service") {
  Component(api, "API слой", "FastAPI Controllers", "HTTP endpoints")
  Component(useCases, "Use Cases", "Application layer", "Сценарии: get/update profile, add/get/update house")
  Component(domain, "Domain Model", "Domain layer", "UserProfile, инварианты")
  Component(repo, "Repository", "Infrastructure", "Доступ к БД")
}

Rel(api, useCases, "Вызывает")
Rel(useCases, domain, "Использует")
Rel(useCases, repo, "Читает/пишет через")
Rel(repo, userDb, "CRUD", "SQL")

@enduml
```