# Measurement Fixture Project

A minimal microservice scaffold used by `scripts/measure.py` and integration tests.

- `src/MeasurementSvc.Api` — gateway endpoint (one `MapGet`)
- `src/MeasurementSvc.Application` — one query interface (`IOrderQueries`)
- `src/MeasurementSvc.Domain` — one aggregate (`Order`)
- `src/MeasurementSvc.Infrastructure` — DI wiring

This fixture is not buildable on its own; the `.cs` files exist so the plugin's
detection + skill-deployment paths have realistic content to render against.
