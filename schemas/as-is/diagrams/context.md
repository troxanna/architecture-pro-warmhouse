# Диаграмма контекста

```puml
@startuml
!includeurl https://raw.githubusercontent.com/RicardoNiepel/C4-PlantUML/master/C4_Component.puml

top to bottom direction

title Тёплый дом — текущая архитектура (As-Is)

Person(user, "Пользователь", "Управляет отоплением и просматривает температуру")

System(warmHome, "Система «Тёплый дом»", "Монолитная система для управления отоплением и просмотра температуры")

System_Ext(sensorApi, "Home Devices API", "Внешняя система для взаимодействия с устройствами дома")

Rel(user, warmHome, "Использует", "Web UI")
Rel(warmHome, sensorApi, "Запрашивает температуру", "REST API")
Rel(warmHome, sensorApi, "Управляет отоплением", "REST API")

@enduml
```

Примечание к диаграмме контекста:

Помимо пользовательского Web UI система предоставляет HTTP API для управления устройствами.
Конкретные клиенты этого API в текущем As-Is описании не определены.

