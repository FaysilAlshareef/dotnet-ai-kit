# Contract: Detection Output Format

**Type**: CLI output contract
**Consumers**: Users running `dotnet-ai init` or `dotnet-ai check`

## Detection Summary Output

When detection completes, the CLI displays:

```
Detected: {project_type} ({architecture_mode})
  Confidence: {high|medium|low} ({score}%)
  Signals:
    + {signal_1_name} ({signal_1_type})
    + {signal_2_name} ({signal_2_type})
    + {signal_3_name} ({signal_3_type})
  .NET Version: {version}
  Packages: {count} found

Is this correct? [Y/n/change]:
```

### User Override Flow

If user types `n` or `change`:

```
Select project type:
  1. command     - Command-side (CQRS write model)
  2. query-sql   - Query-side with SQL storage
  3. query-cosmos - Query-side with Cosmos DB
  4. processor   - Event processor / router
  5. gateway     - API gateway / router
  6. controlpanel - Blazor control panel
  7. hybrid      - Mixed command + query
  8. vsa         - Vertical Slice Architecture
  9. clean-arch  - Clean Architecture
  10. ddd        - Domain-Driven Design
  11. modular-monolith - Modular Monolith
  12. generic    - Generic .NET project

Your choice [1-12]:
```

## Detection Result File (project.yml)

```yaml
detected:
  mode: microservice          # or generic
  project_type: command       # one of the enum values
  dotnet_version: "net8.0"
  architecture: "CQRS Command Side"
  namespace_format: "{Company}.{Domain}.{Side}.{Layer}"
  packages:
    - MediatR
    - Microsoft.EntityFrameworkCore
  confidence: high
  confidence_score: 0.92
  user_override: null         # or the overridden type
  top_signals:
    - name: "AggregateRoot base class"
      type: code-pattern
      confidence: high
    - name: "Domain event definitions"
      type: code-pattern
      confidence: high
    - name: "OutboxMessage usage"
      type: code-pattern
      confidence: medium
```
