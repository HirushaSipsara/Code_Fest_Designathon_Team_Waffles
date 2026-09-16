# Simulation boundaries

## Real implementation

- React/Vite/TypeScript frontend API integration
- FastAPI route, Pydantic schema and deterministic policy validation
- PostgreSQL persistence for CP3 devices, confirmed scenes and audit activity
- Configurable OpenAI-compatible AI HTTP request when environment configuration exists
- deterministic automation routing and confirmed-scene execution
- `DeviceService` and replaceable `DeviceAdapter` boundary

## Simulated

- AC, lights, curtains, television and lock state changes
- device latency and acknowledgement
- `MockDeviceAdapter` command/state behaviour and requested/acknowledged lifecycle
- resident-arrival event trigger
- prototype visitor scanner, facility booking/payment, maintenance and operator actions until their P1/P2 APIs are connected

## Seeded/demo-only

- energy/bill history and analytics
- developer portfolio metrics and fleet health examples
- initial passes, activity and maintenance examples in the source prototype
- original fixed phrase NL examples (replaced in the CP3 app, retained only in the untouched reference)
