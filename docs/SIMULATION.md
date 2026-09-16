# Simulation boundaries

## Real implementation

- React/Vite/TypeScript frontend API integration
- FastAPI route, Pydantic schema and deterministic policy validation
- PostgreSQL persistence for CP3 devices, confirmed scenes and audit activity
- offline seeded natural-language matching and deterministic insight analytics
- in-process telemetry event ingestion and persistence
- deterministic automation routing and confirmed-scene execution
- `DeviceService` and replaceable `DeviceAdapter` boundary

## Simulated

- AC, lights, curtains, television and lock state changes
- device latency and acknowledgement
- `MockDeviceAdapter` command/state behaviour and requested/acknowledged lifecycle
- resident-arrival and telemetry event stream
- prototype visitor scanner, facility booking/payment, maintenance and operator actions until their P1/P2 APIs are connected

## Seeded/demo-only

- seven-day energy, battery and arrival/action histories
- developer portfolio metrics and fleet health examples
- initial passes, activity and maintenance examples in the source prototype
- 15 backend natural-language intent groups used by the offline demo
