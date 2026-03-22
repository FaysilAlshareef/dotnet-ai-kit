# Quickstart: Plugin Ecosystem v1.0

## For Users

### Install via Claude Code Plugin Marketplace

```bash
# Add the marketplace (one-time)
/plugin marketplace add FaysilAlshareef/dotnet-ai-kit

# Install the plugin
/plugin install dotnet-ai-kit
```

All 26 commands, 104 skills, 13 agents, 6 rules, and 4 hooks are immediately available.

### Optional: Install C# Language Intelligence

```bash
dotnet tool install -g csharp-ls
```

This enables semantic code navigation (go-to-definition, find references, diagnostics) via MCP, reducing token usage by ~10x compared to grep-based analysis.

### Verify Installation

```
/dotnet-ai.status
```

### Disable a Hook

If auto-formatting is disruptive during rapid prototyping, disable it in Claude Code settings:

```json
{
  "hooks": {
    "post-edit-format": { "enabled": false }
  }
}
```

## For Developers (contributing to the plugin)

### Setup

```bash
git clone https://github.com/FaysilAlshareef/dotnet-ai-kit.git
cd dotnet-ai-kit
pip install -e ".[dev]"
pytest
```

### Validate Plugin Structure

```bash
# Verify plugin.json exists and is valid
python -c "import json; json.load(open('.claude-plugin/plugin.json'))"

# Verify all SKILL.md files have required frontmatter
python -c "
from pathlib import Path
import yaml
for f in Path('skills').rglob('SKILL.md'):
    with open(f) as fh:
        content = fh.read()
    fm = content.split('---')[1]
    data = yaml.safe_load(fm)
    assert 'name' in data, f'{f}: missing name'
    assert 'description' in data, f'{f}: missing description'
    assert data['name'].startswith('dotnet-ai-'), f'{f}: name must start with dotnet-ai-'
print('All SKILL.md files valid')
"
```

### Run Tests

```bash
pytest --cov=dotnet_ai_kit
ruff check src/ tests/
ruff format --check src/ tests/
```
