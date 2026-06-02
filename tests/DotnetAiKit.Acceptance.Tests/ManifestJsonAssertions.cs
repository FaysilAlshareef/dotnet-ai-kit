using System.Text.Json;
using Xunit;

namespace DotnetAiKit.Acceptance.Tests;

internal static class ManifestJsonAssertions
{
    public static JsonDocument ParseFile(string path)
    {
        Assert.True(File.Exists(path), $"Expected manifest file to exist: {path}");
        return JsonDocument.Parse(File.ReadAllText(path));
    }

    public static IReadOnlyList<string> ReadStringArray(JsonElement root, string propertyName)
    {
        if (!root.TryGetProperty(propertyName, out var value) || value.ValueKind != JsonValueKind.Array)
            return [];

        return value.EnumerateArray()
            .Where(item => item.ValueKind == JsonValueKind.String)
            .Select(item => item.GetString()!)
            .ToArray();
    }
}
