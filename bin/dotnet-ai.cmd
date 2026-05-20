@echo off
REM Feature 019 / OOS-003 / commit 27 / T180: Windows source-tree wrapper for
REM dotnet-ai. End users should install the wheel (`pip install dotnet-ai-kit`
REM or `uv tool install dotnet-ai-kit`) and rely on the `[project.scripts]`
REM entry point. This wrapper exists for contributors working out of a
REM fresh git clone before `pip install -e .` lands.
REM
REM Standalone-executable packaging (shiv / PyInstaller) is deferred to
REM v1.1 per OOS-003.
@python -m dotnet_ai_kit.cli %*
