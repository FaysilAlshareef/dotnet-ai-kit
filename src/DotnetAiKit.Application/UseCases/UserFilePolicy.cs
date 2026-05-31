using System.Text.Json;
using System.Text.Json.Nodes;

namespace DotnetAiKit.Application.UseCases;

/// <summary>What happened to a user-owned file on write (maps to <c>HostWriteResult</c> buckets).</summary>
public enum UserFileAction
{
    /// <summary>The file was absent and was written fresh.</summary>
    Written,

    /// <summary>Present but byte-equal to the managed render — refreshed (no user content at risk).</summary>
    Refreshed,

    /// <summary>Present + user-edited; managed keys were deep-merged in without dropping user keys.</summary>
    Merged,

    /// <summary>Present + user-edited + not safely mergeable (or invalid JSON) — left in place, backed up, consent pending.</summary>
    PendingConsent,
}

/// <summary>
/// The user-owned-file policy (FR-022-13/14, AR-7b): never silently clobber a file a user may have edited
/// (<c>.claude/settings.json</c>, <c>AGENTS.md</c>, …). Pure decision over (existing, managed) content; the
/// host adapter performs the I/O + backup and records the action in <c>HostWriteResult</c>.
/// </summary>
public static class UserFilePolicy
{
    public static (UserFileAction Action, string Content) Decide(string? existing, string managed, bool isJson)
    {
        if (existing is null)
            return (UserFileAction.Written, managed);

        if (Normalize(existing) == Normalize(managed))
            return (UserFileAction.Refreshed, managed);

        if (isJson && TryDeepMerge(existing, managed, out var merged))
            return (UserFileAction.Merged, merged);

        // User-edited and not safely mergeable (or invalid JSON): keep the user's content, back up, ask consent.
        return (UserFileAction.PendingConsent, existing);
    }

    private static string Normalize(string text) => text.Replace("\r\n", "\n").Trim();

    private static bool TryDeepMerge(string existingJson, string managedJson, out string merged)
    {
        merged = string.Empty;
        try
        {
            if (JsonNode.Parse(existingJson) is not JsonObject existing || JsonNode.Parse(managedJson) is not JsonObject managed)
                return false;
            MergeInto(existing, managed);
            merged = existing.ToJsonString(new JsonSerializerOptions { WriteIndented = true }) + "\n";
            return true;
        }
        catch (JsonException)
        {
            return false; // invalid JSON → PendingConsent (back up + warn)
        }
    }

    /// <summary>Adds managed keys missing from the user object; recurses into nested objects; user values win on conflict.</summary>
    private static void MergeInto(JsonObject target, JsonObject source)
    {
        foreach (var (key, value) in source)
        {
            if (!target.ContainsKey(key))
                target[key] = value?.DeepClone();
            else if (target[key] is JsonObject targetObj && value is JsonObject sourceObj)
                MergeInto(targetObj, sourceObj);
            // else: the user's value is kept (managed only fills gaps).
        }
    }
}
