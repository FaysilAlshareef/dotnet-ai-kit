# Contract: Hook launcher / backend resolution (FR-022-10/11/12)

The shape of the generated Claude `hooks.json` command and how the v2 backend is resolved at fire time.

## Generated command (in `build/claude/hooks/hooks.json`)

```json
{
  "hooks": {
    "PreToolUse": [{ "matcher": "Edit|Write|MultiEdit",
      "hooks": [{ "type": "command", "command": "dotnet-ai hook pretooluse" }] }],
    "Stop":         [{ "hooks": [{ "type": "command", "command": "dotnet-ai hook stop" }] }],
    "SubagentStop": [{ "hooks": [{ "type": "command", "command": "dotnet-ai hook stop" }] }]
  }
}
```

- The command is the **global `dotnet-ai` tool** (`DotnetAiKit.Tool`). It is the backend; the plugin does not bundle it.
- A T2 `prompt`-type PreToolUse entry is added in F7 (FR-022-15), Claude-scoped.

## Resolution contract

| Condition | Behavior |
|---|---|
| v2 `dotnet-ai` first on PATH | hook runs; emits valid hook protocol on stdout |
| backend unresolved / errors | **fail safe**: exit 0, no `decision:block`, clear stderr — never wedge the session (FR-022-12) |
| `init`/`check` run + a `dotnet-ai` on PATH is NOT the v2 tool (e.g. `…/Python*/Scripts/dotnet-ai*`) | warn: shadowing shim detected + remediation (install/repath the v2 tool) (FR-022-10) |

## Smoke contract (FR-022-11)

`echo '<payload>' | <generated-command>` MUST:
- PreToolUse generated-file payload → `{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny",...}}`
- PreToolUse normal path, no rules → empty (allow)
- Stop with `{"stop_hook_active":true}` → empty (allow; no wedge)
- Stop in a red-build dir → `{"decision":"block","reason":...}`

A test asserts the generated command string (not a hand-built one) produces this — proving runnability, not just discovery.
