using DotnetAiKit.Application.Ports;
using Spectre.Console;

namespace DotnetAiKit.Cli.Output;

/// <summary>
/// The one place Spectre.Console is referenced (FR-C3). Use-cases stay UI-free behind
/// <see cref="IConsoleReporter"/>; warnings/errors go to stderr.
/// </summary>
internal sealed class SpectreConsoleReporter : IConsoleReporter
{
    private static readonly IAnsiConsole Err = AnsiConsole.Create(new AnsiConsoleSettings
    {
        Out = new AnsiConsoleOutput(Console.Error),
    });

    public void Info(string message) => AnsiConsole.MarkupLineInterpolated($"{message}");

    public void Success(string message) => AnsiConsole.MarkupLineInterpolated($"[green]✓[/] {message}");

    public void Warn(string message) => Err.MarkupLineInterpolated($"[yellow]warning:[/] {message}");

    public void Error(string message) => Err.MarkupLineInterpolated($"[red]error:[/] {message}");

    public void Table(string title, IReadOnlyList<(string Key, string Value)> rows)
    {
        var table = new Table { Title = new TableTitle(title) }.AddColumns("Key", "Value");
        foreach (var (key, value) in rows)
            table.AddRow(Markup.Escape(key), Markup.Escape(value));
        AnsiConsole.Write(table);
    }
}
