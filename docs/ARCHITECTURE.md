# Architecture

```text
React frontend
    | REST
FastAPI modular monolith
    |-- AIService (OpenAI-compatible structured parser; proposal only)
    |-- SceneService -> Pydantic + policy checks -> PostgreSQL scene
    |-- AutomationService -> DeviceService -> simulated acknowledgement
    `-- ActivityService -> PostgreSQL audit events
```

PostgreSQL stores `devices` (prototype device state), `scenes` (confirmed trigger/conditions/actions) and `activity_events`. No microservices, MQTT broker or physical-hardware claims are introduced. A future real-IoT adapter belongs behind `DeviceService`.
