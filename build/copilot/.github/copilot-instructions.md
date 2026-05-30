# Copilot Instructions

## security

# Security (universal)

- Use parameterized queries; never concatenate SQL.
- No hardcoded secrets or connection strings; read from configuration.
- No `async void` (except event handlers); no empty `catch` blocks.
- Validate and encode all external input.

