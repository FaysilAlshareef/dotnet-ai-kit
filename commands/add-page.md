---
description: "Add a Blazor page with data grid, filters, and gateway facade to the control panel"
---

# Add Page

Create a Blazor page in the control panel project with MudDataGrid, filter model, gateway facade methods, and optional dialogs.

## Usage

```
/dotnet-ai.add-page $ARGUMENTS
```

**Examples:**
- `Orders` -- Create Orders page with table and filters
- `Orders --module Sales` -- Specify the module/section
- `Orders --operations "list,create,edit,delete"` -- Page capabilities
- `Orders --preview` -- Show code without writing
- `Orders --dry-run` -- Show file list only
- `Orders --verbose` -- Show detection details

## Flags

| Flag | Description |
|------|-------------|
| `--module {ModuleName}` | Module or section for the page (detected or prompted if omitted) |
| `--operations "op1,op2,..."` | Page capabilities (default: list,create) |
| `--preview` | Display generated code without writing to disk |
| `--dry-run` | List files that would be created/modified |
| `--verbose` | Show detection steps and pattern matching details |

## Pre-Generation

1. **Detect project type** -- scan for Blazor markers: `.razor` files, `MudBlazor`, `ResponseResult<T>`.
   - If not a control panel project: report error and stop.
2. **Detect .NET version** -- read `<TargetFramework>`.
3. **Learn patterns from existing pages:**
   - MudBlazor version and component usage patterns
   - Gateway facade pattern (how API calls are structured)
   - Filter model pattern (`QueryStringBindable` usage)
   - Dialog patterns (create/edit dialogs)
   - Menu registration pattern
   - Service collection registration pattern
4. **Detect module** -- if `--module` not provided, scan existing page structure and ask user.
5. **Load config** -- read `.dotnet-ai-kit/config.yml`.

## Skills to Read

- `skills/microservice/controlpanel/blazor-component` -- page structure, code-behind pattern
- `skills/microservice/controlpanel/gateway-facade` -- facade class, Management sub-class
- `skills/microservice/controlpanel/mudblazor-patterns` -- MudDataGrid, dialogs, expansion panels
- `skills/microservice/controlpanel/query-string-bindable` -- filter model, URL state binding

## Generation Flow

Parse `$ARGUMENTS` to extract `{PageName}` (PascalCase plural). Derive singular form for entity references.

### Step 1: Generate Gateway Facade
- If module gateway exists (`API/{Module}/{Module}Gateway.cs`): add new Management sub-class
- If new module: create gateway class with Management
- Path: `API/{Module}/{Module}Gateway.cs` (create or modify)
- Path: `API/{Module}/{Module}Management.cs` (if separate file pattern)
- Methods: `GetAllAsync`, `GetByIdAsync`, `CreateAsync`, `UpdateAsync`, `DeleteAsync`
- Each method calls gateway HTTP client and returns `ResponseResult<T>`

### Step 2: Generate Filter Model
- Path: `Presentation/{Module}/{PageName}FilterModel.cs`
- Extends `QueryStringBindable`
- Properties with `UpdateQueryStringIfChanged` for URL binding
- `ToQuery()` method mapping filters to query parameters

### Step 3: Generate Blazor Page
- Path: `Presentation/{Module}/{PageName}Page.razor`
- Path: `Presentation/{Module}/{PageName}Page.razor.cs` (code-behind)
- `MudDataGrid` with `ServerData` callback for server-side pagination
- Filter panel with `MudExpansionPanels`
- `BindToNavigationManager` for URL state synchronization
- Gateway call with `Switch` result pattern for success/error handling
- Dialog triggers for create/edit if operations include them

### Step 4: Generate Dialogs (if operations include create/edit)
- Path: `Presentation/{Module}/Dialogs/Create{Singular}Dialog.razor`
- Path: `Presentation/{Module}/Dialogs/Edit{Singular}Dialog.razor` (if edit included)
- `MudDialog` with form fields
- Validation via `MudForm`
- Gateway call on submit

### Step 5: Register in Application
- Add menu item to navigation/menu registration
- Register gateway facade in service collection
- Follow existing registration patterns exactly

## Post-Generation

1. **Run `dotnet build`** -- verify compilation.
2. **Report generated files.**
3. **Note:** No tests are generated for control panel pages -- testing is at the gateway level.
4. **Suggest next steps:**
   ```
   Page '{PageName}' created in {Module} module.
   Next: Run the control panel to verify the page renders correctly.
   ```

## Preview / Dry-Run Behavior

- `--preview`: Show all generated code with file path headers. No writes.
- `--dry-run`: List files only. No code output, no writes.
