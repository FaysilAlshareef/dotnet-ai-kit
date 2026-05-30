# Contract: `check` exit codes (preserved from v1 — NFR-7 / FR-014)

`dotnet-ai check` is **read-only** (never mutates files), makes **no network calls**, and returns a fixed, enumerated exit code. On multiple failures, **the lowest non-zero code wins**.

| Code | Meaning | Check class |
|---|---|---|
| `0` | All checks pass | — |
| `10` | Plugin install missing | per configured host |
| `11` | External binary missing | host CLI / git probes |
| `12` | `project.yml` schema invalid | per-solution config |
| `13` | Detected-path inconsistency | detection vs. config |
| `14` | Manifest integrity failure | sha256 / traversal guard |
| `15` | Copilot render stale | render-only host drift |
| `16` | Host symmetry / loader failure | cross-host invariants |
| `99` | Unknown error | catch-all |

**Acceptance (Acceptance.Tests)**: each code is produced by a fixture project in the corresponding broken state; a healthy fixture returns `0`; "lowest code wins" is asserted by a fixture failing two classes at once. This is part of SC-007 and ports the v1 contract near-verbatim.
