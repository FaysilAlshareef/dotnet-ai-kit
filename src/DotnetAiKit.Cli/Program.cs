namespace DotnetAiKit.Cli;

/// <summary>
/// CLI composition root. The P0 stub prints a banner; the System.CommandLine root-command
/// tree and manual DI wiring are introduced in P3 (generate) / P5 (all verbs).
/// </summary>
internal static class Program
{
    public static int Main(string[] args)
    {
        Console.WriteLine("dotnet-ai (v2 scaffold)");
        return 0;
    }
}
