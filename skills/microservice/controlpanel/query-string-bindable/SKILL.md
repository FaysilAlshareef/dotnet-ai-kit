---
name: query-string-bindable
description: >
  URL-synchronized filter models for control panel data grids. Covers
  QueryStringBindable base class, two-way URL binding, and PropertyChanged notification.
  Trigger: query string, URL filter, bindable, filter model, URL sync.
metadata:
  category: microservice/controlpanel
  agent: controlpanel-architect
---

# QueryStringBindable — URL-Synchronized Filters

## Core Principles

- Filter changes update the browser URL (bookmarkable, shareable state)
- URL changes restore filter state (back/forward navigation works)
- `QueryStringBindable` base class handles two-way binding
- `INotifyPropertyChanged` triggers UI updates on filter changes
- Debounce text fields to avoid excessive API calls
- `ToQuery()` maps filter model to API query parameters

## Key Patterns

### QueryStringBindable Base Class

```csharp
namespace {Company}.{Domain}.ControlPanel.Models;

public abstract class QueryStringBindable : INotifyPropertyChanged
{
    public event PropertyChangedEventHandler? PropertyChanged;

    protected void OnPropertyChanged([CallerMemberName] string? name = null)
        => PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(name));

    public void BindToNavigationManager(NavigationManager nav)
    {
        var uri = new Uri(nav.Uri);
        var query = QueryHelpers.ParseQuery(uri.Query);
        LoadFromQuery(query);

        PropertyChanged += (_, args) =>
        {
            var queryString = ToQueryString();
            var baseUri = uri.GetLeftPart(UriPartial.Path);
            nav.NavigateTo($"{baseUri}{queryString}", replace: true);
        };
    }

    protected abstract void LoadFromQuery(
        Dictionary<string, StringValues> query);

    protected abstract string ToQueryString();
}
```

### Filter Model Implementation

```csharp
namespace {Company}.{Domain}.ControlPanel.Models;

public sealed class OrderFilterModel : QueryStringBindable
{
    private string? _search;
    private int _page = 1;
    private int _pageSize = 20;
    private string? _status;
    private string? _sortBy;

    public string? Search
    {
        get => _search;
        set { _search = value; OnPropertyChanged(); }
    }

    public int Page
    {
        get => _page;
        set { _page = value; OnPropertyChanged(); }
    }

    public int PageSize
    {
        get => _pageSize;
        set { _pageSize = value; OnPropertyChanged(); }
    }

    public string? Status
    {
        get => _status;
        set { _status = value; OnPropertyChanged(); }
    }

    public string? SortBy
    {
        get => _sortBy;
        set { _sortBy = value; OnPropertyChanged(); }
    }

    protected override void LoadFromQuery(
        Dictionary<string, StringValues> query)
    {
        if (query.TryGetValue("search", out var search))
            _search = search;
        if (query.TryGetValue("page", out var page) && int.TryParse(page, out var p))
            _page = p;
        if (query.TryGetValue("pageSize", out var ps) && int.TryParse(ps, out var s))
            _pageSize = s;
        if (query.TryGetValue("status", out var status))
            _status = status;
        if (query.TryGetValue("sortBy", out var sortBy))
            _sortBy = sortBy;
    }

    protected override string ToQueryString()
    {
        var parts = new List<string>();
        if (!string.IsNullOrEmpty(_search)) parts.Add($"search={Uri.EscapeDataString(_search)}");
        if (_page != 1) parts.Add($"page={_page}");
        if (_pageSize != 20) parts.Add($"pageSize={_pageSize}");
        if (!string.IsNullOrEmpty(_status)) parts.Add($"status={_status}");
        if (!string.IsNullOrEmpty(_sortBy)) parts.Add($"sortBy={_sortBy}");
        return parts.Count > 0 ? "?" + string.Join("&", parts) : "";
    }

    public GetOrdersRequest ToApiRequest() => new()
    {
        Page = Page,
        PageSize = PageSize,
        Search = Search,
        Status = Status,
        SortBy = SortBy
    };
}
```

### Blazor Page Integration

```razor
@page "/orders"
@inject NavigationManager NavigationManager

@code {
    private OrderFilterModel _filter = new();
    private MudDataGrid<OrderSummaryResponse>? _dataGrid;

    protected override void OnInitialized()
    {
        _filter.BindToNavigationManager(NavigationManager);
        _filter.PropertyChanged += async (_, _) =>
        {
            if (_dataGrid is not null)
                await _dataGrid.ReloadServerData();
        };
    }
}
```

## Anti-Patterns

| Anti-Pattern | Correct Approach |
|---|---|
| Filter state not in URL | Use QueryStringBindable for shareable URLs |
| Missing debounce on text fields | Debounce search fields (300ms) |
| Full page reload on filter change | Use `NavigateTo` with `replace: true` |
| Loading query from URL in every render | Load once in OnInitialized |

## Detect Existing Patterns

```bash
# Find QueryStringBindable
grep -r "QueryStringBindable" --include="*.cs" src/ControlPanel/

# Find filter models
grep -r "FilterModel\|Filter.*: QueryString" --include="*.cs" src/ControlPanel/

# Find BindToNavigationManager
grep -r "BindToNavigationManager" --include="*.razor" src/ControlPanel/
```

## Adding to Existing Project

1. **Use existing `QueryStringBindable` base** class
2. **Follow naming convention**: `{Entity}FilterModel`
3. **Add properties** with backing fields and `OnPropertyChanged()`
4. **Wire up in `OnInitialized`** with `BindToNavigationManager`
5. **Connect `PropertyChanged`** to data grid reload
