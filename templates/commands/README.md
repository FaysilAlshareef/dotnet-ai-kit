# Command File Templates

Templates for AI tool command files used by the dotnet-ai-kit CLI.

## Template Format

Command templates use the `$ARGUMENTS` placeholder to accept user input at invocation time.
The CLI's copier generates tool-specific command files from these templates:

- `.claude/commands/dotnet-ai.specify.md` (for Claude)
- `.cursor/commands/dotnet-ai.specify.md` (for Cursor)
- etc.

## Placeholders

- `$ARGUMENTS` - Replaced with the user's input when the command is invoked
- `{{ company }}` - Replaced with the company name from config.yml
- `{{ domain }}` - Replaced with the domain name from the feature spec

## Usage

These templates are copied and customized by `dotnet-ai init` and `dotnet-ai implement`
to create project-specific command files for the configured AI tools.
