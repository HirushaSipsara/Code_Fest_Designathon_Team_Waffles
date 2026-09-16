# CP3 architecture

```text
React/Vite
    | REST
FastAPI route
    |-- AIService
    |     `-- AIProvider interface
    |           `-- OpenAICompatibleProvider -> configured LLM
    |-- Pydantic schema validation
    |-- deterministic policy validation
    |-- SceneService -> PostgreSQL scenes/drafts/audit
    `-- AutomationEngine
           `-- DeviceService
                  `-- DeviceAdapter interface
                         `-- MockDeviceAdapter / emulator
                                `-- simulated AC / lights / curtains / lock / TV
```

AI produces only a proposal. It has no database or device dependency. The application validates and stores the proposal; only confirmed scenes can reach the automation engine.

## Device boundary

Hackathon: `DeviceService → MockDeviceAdapter`

Future pilot: `DeviceService → MQTTDeviceAdapter → Real IoT Gateway`

Automation depends on `DeviceService`, never the mock implementation. `MockDeviceAdapter` implements supported prototype state changes and returns an acknowledgement after simulated latency. No physical hardware or MQTT broker is claimed.
