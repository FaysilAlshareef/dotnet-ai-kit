# Contract: Cursor Plugin Delivery

## Purpose

Ensure Cursor generated output is structurally valid and manifest references resolve.

## Target Shape

```text
build/cursor/
|-- .cursor-plugin/
|   `-- plugin.json
|-- agents/
|   `-- <agent>.md
|-- commands/
|   `-- <command>.md
|-- rules/
|   `-- <rule>.mdc
`-- skills/
    `-- <skill>/SKILL.md
```

## Required Behavior

- Cursor manifest is emitted under the Cursor plugin root.
- If the manifest lists `./agents/<name>.md`, generation emits that file.
- Agent files use Cursor-compatible frontmatter: `name` and `description`.
- Manifest references are resolved relative to the plugin root.

## Verification

- Host projector test asserts Cursor agents are emitted.
- Acceptance test parses the Cursor manifest and verifies every referenced file exists.
- Generation remains drift-clean.
