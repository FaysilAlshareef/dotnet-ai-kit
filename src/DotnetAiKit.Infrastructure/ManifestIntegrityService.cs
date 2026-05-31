using System.Security.Cryptography;
using System.Text;

namespace DotnetAiKit.Infrastructure;

/// <summary>
/// sha256 integrity over manifest/content (NFR-7; ports the v1 manifest.py design). Newline-normalized
/// so the hash is stable across platforms. Used to detect tampering / drift of the committed manifest.
/// </summary>
public sealed class ManifestIntegrityService
{
    public string ComputeSha256(string content)
    {
        var normalized = (content ?? string.Empty).Replace("\r\n", "\n");
        var bytes = SHA256.HashData(Encoding.UTF8.GetBytes(normalized));
        return Convert.ToHexString(bytes).ToLowerInvariant();
    }

    public bool Verify(string content, string expectedSha256) =>
        string.Equals(ComputeSha256(content), (expectedSha256 ?? string.Empty).Trim().ToLowerInvariant(), StringComparison.Ordinal);
}
