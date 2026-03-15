# dotnet-ai-kit - Review System & CodeRabbit Integration

## Review Philosophy

Reviews happen at two levels:
1. **Standards Review** (always) - Against company patterns and conventions
2. **AI Review** (optional) - CodeRabbit CLI for deeper analysis

## Standards Review Checklist

### Architecture & Patterns
- [ ] Layer dependencies correct (Domain → Application → Infra → Grpc)
- [ ] Aggregate follows Aggregate<T> pattern with ApplyChange
- [ ] Events use Event<TData> with proper sequence
- [ ] Outbox pattern used for publishing (not direct send)
- [ ] Query entities use private setters with CTO constructors
- [ ] Event handlers check sequence strictly
- [ ] Service bus listener uses session processor
- [ ] Gateway controllers inject gRPC clients (not HttpClient)
- [ ] Control panel uses ResponseResult<T>.Switch pattern

### Naming Conventions
- [ ] Project naming: {Company}.{Domain}.{Side}.{Layer}
- [ ] Aggregate: PascalCase singular
- [ ] Events: {Aggregate}{Action} (e.g., OrderCreated)
- [ ] Event data: {EventName}Data record
- [ ] Handlers: {Name}Handler
- [ ] Proto files: snake_case.proto
- [ ] Proto services: {Domain}{Side} (e.g., OrderCommands)

### Localization
- [ ] NO plain strings in gRPC responses
- [ ] ALL user-facing text uses Phrases.{Key}
- [ ] Both Phrases.resx and Phrases.en.resx updated
- [ ] EntitiesLocalization for display names

### Error Handling
- [ ] Domain exceptions implement IProblemDetailsProvider
- [ ] gRPC services use ApplicationExceptionInterceptor
- [ ] Idempotent handlers return true for AlreadyExists
- [ ] Control panel uses Switch with onSuccess/onFailure

### Testing
- [ ] Fakers use CustomConstructorFaker<T>
- [ ] Assertions in static extension classes
- [ ] Integration tests use WebApplicationFactory
- [ ] Full cycle: endpoint → handler → aggregate → event → outbox
- [ ] Query tests verify sequence checking

### Security
- [ ] No hardcoded connection strings or secrets
- [ ] Authorization policies on gateway endpoints
- [ ] AccessClaims extracted properly in gRPC services
- [ ] No secrets in K8s manifests (use secretKeyRef)

### DevOps
- [ ] K8s manifest has all required env vars
- [ ] Dockerfile uses multi-stage build
- [ ] GitHub Actions has build and deploy jobs
- [ ] Service bus topics/subscriptions configured

---

## CodeRabbit CLI Integration

### Detection
```bash
# Check if coderabbit is installed
which coderabbit 2>/dev/null
# or
coderabbit --version
```

### Usage (when available)
```bash
# Review current branch against base
coderabbit review --base main --head feature/001-orders

# Review specific files
coderabbit review --files "src/Domain/Aggregates/Order.cs,src/Application/Commands/*"
```

### Integration Flow
1. Run standards review first (our patterns)
2. Run CodeRabbit if available
3. Merge findings:
   - Deduplicate (same issue found by both)
   - Prioritize standards review for pattern violations
   - Prioritize CodeRabbit for logic/security issues
4. Present unified report

### Configuration
```yaml
# .dotnet-ai-kit/config.yml
integrations:
  coderabbit:
    enabled: true          # false to skip even if installed
    auto_fix: false        # true to auto-apply suggestions
    severity_threshold: warning  # minimum severity to report
```

### When CodeRabbit is NOT installed
```
Standards Review: COMPLETE (5 findings)
CodeRabbit Review: SKIPPED (not installed)

Tip: Install CodeRabbit CLI for deeper AI-powered review:
  npm install -g coderabbit
  coderabbit auth login
```

---

## Review Report Format

```markdown
## Review Report: feature/001-order-management

### Summary
Reviewed changes across 4 repos. 2 issues need fixing.

### Per-Repo Results

#### Command Repo: company-order-commands
| Category | Status | Findings |
|----------|--------|----------|
| Architecture | PASS | - |
| Naming | PASS | - |
| Localization | WARN | 1 missing Phrases key |
| Error Handling | PASS | - |
| Testing | PASS | - |
| CodeRabbit | PASS | 1 suggestion (non-blocking) |

**Findings:**
1. [WARN] `OrderService.cs:45` - Response uses plain string "Order created"
   → Fix: Add `Phrases.OrderCreated` to resource files

2. [SUGGESTION] `OrderAggregate.cs:23` - Consider sealed class
   → Source: CodeRabbit

#### Query Repo: company-order-queries
| Category | Status | Findings |
|----------|--------|----------|
| Architecture | PASS | - |
| Event Handlers | FAIL | 1 missing sequence check |
| Naming | PASS | - |
| Testing | WARN | 1 missing test case |

**Findings:**
1. [FAIL] `OrderUpdatedHandler.cs:18` - Missing strict sequence validation
   → Fix: Add `if (entity.Sequence != @event.Sequence - 1) return ...`

2. [WARN] Missing test for out-of-order event handling

### Auto-Fix Available
2 issues can be auto-fixed. Apply? [Y/n]
```

---

## Review Triggers

The review command can be triggered:
1. **Manually**: `/dotnet-ai.review`
2. **After implement**: Part of the lifecycle flow
3. **Before PR**: Automatically suggested before `/dotnet-ai.pr`
4. **On existing changes**: Review any branch against standards
