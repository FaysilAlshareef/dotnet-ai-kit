using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using DotnetAiKit.Application.Ports;

namespace DotnetAiKit.Infrastructure;

/// <summary>
/// sha256 integrity over manifest/content (NFR-7; ports the v1 manifest.py design). Newline-normalized
/// so the hash is stable across platforms. Used to detect tampering / drift of the committed manifest.
/// </summary>
public sealed class ManifestIntegrityService : IManifestIntegrity
{
    public string ComputeSha256(string content)
    {
        var normalized = (content ?? string.Empty).Replace("\r\n", "\n");
        var bytes = SHA256.HashData(Encoding.UTF8.GetBytes(normalized));
        return Convert.ToHexString(bytes).ToLowerInvariant();
    }

    public bool Verify(string content, string expectedSha256) =>
        string.Equals(ComputeSha256(content), (expectedSha256 ?? string.Empty).Trim().ToLowerInvariant(), StringComparison.Ordinal);

    public string ComputeFootprintSha256(string host, int rules) =>
        ComputeSha256($"host: {host}\nrules: {rules}\n");

    public bool TryVerifyFootprintManifest(string manifestJson, out string details)
    {
        try
        {
            using var document = JsonDocument.Parse(manifestJson);
            var root = document.RootElement;
            var host = root.GetProperty("host").GetString() ?? string.Empty;
            var rules = root.GetProperty("rules").GetInt32();
            var expected = root.GetProperty("sha256").GetString() ?? string.Empty;
            var actual = ComputeFootprintSha256(host, rules);
            if (Verify($"host: {host}\nrules: {rules}\n", expected))
            {
                details = string.Empty;
                return true;
            }

            details = $"manifest hash mismatch: expected {expected}, actual {actual}.";
            return false;
        }
        catch (Exception ex) when (ex is JsonException or InvalidOperationException or KeyNotFoundException)
        {
            details = "manifest is invalid: " + ex.Message;
            return false;
        }
    }
}
