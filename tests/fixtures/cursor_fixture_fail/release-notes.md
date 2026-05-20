# Release Notes (Cursor FAIL branch fixture)

## v1.0 Highlights

- **Cursor sub-agent generation deferred to v1.1**: The A-005 spike fixture
  failed under Cursor's loader. Per cursor-fixture-decision.contract.md, the
  release scope was revised: Cursor manifest's `agents` field removed,
  spec updated, and `generate_cursor_agent()` will raise NotImplementedError
  until the spike passes in a follow-up release.
