# Contract: Manifest Integrity

## Purpose

Make the `check` command's `manifest-integrity` result truthful.

## Required Behavior

- Missing `.dotnet-ai-kit/manifest.json` fails with a missing-manifest message.
- Valid manifest contents pass integrity verification.
- Tampered manifest contents fail integrity verification.
- The result uses the documented manifest-integrity exit code.
- The check remains read-only and makes no network calls.

## Compatibility

If the current manifest format cannot support a stored expected hash without a format change, the implementation must either:

- Add a deterministic compatible field or sidecar representation and test it, or
- Rename the check to `manifest-present` and explicitly record full integrity verification as deferred.

## Verification

- Unit or acceptance tests cover valid, missing, and tampered manifests.
- Existing check contract tests continue to pass or are updated to the new truthful contract.
