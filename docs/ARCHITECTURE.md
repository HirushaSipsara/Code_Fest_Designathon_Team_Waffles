# LIVLINK architecture

```text
Simulated device publisher
    | in-process event bus (asyncio.Queue)
    v
Telemetry subscriber
    |-- PostgreSQL telemetry / resident events
    |-- energy baseline + anomaly threshold
    |-- maintenance weighted risk score
    `-- arrival pattern counter
             |
             v
FastAPI local REST API <---- React/Vite
    |-- insight list / dismiss / accept
    |-- seeded natural-language scene matcher
    |-- Pydantic + deterministic policy validation
    |-- SceneService -> PostgreSQL scenes/drafts/audit
    `-- AutomationEngine
           `-- DeviceService
                  `-- DeviceAdapter interface
                         `-- MockDeviceAdapter / emulator
                                `-- simulated AC / lights / curtains / lock / TV
```

The hackathon path is fully local and offline. The React app talks to the local FastAPI backend; this is the application API, not an external AI service. There is no API key, external LLM, Mosquitto broker or physical hardware.

## Device boundary

Hackathon: `DeviceService → MockDeviceAdapter`

Future pilot: `DeviceService → MQTTDeviceAdapter → Real IoT Gateway`

Application services depend on `DeviceService`, never simulator internals. This keeps the production replacement path visible without pretending it is implemented now.
