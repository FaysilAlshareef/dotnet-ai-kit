using DotnetAiKit.Application.UseCases;
using Xunit;

namespace DotnetAiKit.Application.Tests;

/// <summary>FR-022-13/14: the user-owned-file policy never silently clobbers user content.</summary>
public class UserFilePolicyTests
{
    private const string Managed = "{\n  \"$schema\": \"https://json.schemastore.org/claude-code-settings.json\"\n}\n";

    [Fact]
    public void Absent_file_is_written_fresh()
    {
        var (action, content) = UserFilePolicy.Decide(existing: null, Managed, isJson: true);
        Assert.Equal(UserFileAction.Written, action);
        Assert.Equal(Managed, content);
    }

    [Fact]
    public void Unchanged_managed_file_is_refreshed()
    {
        var (action, _) = UserFilePolicy.Decide(existing: Managed, Managed, isJson: true);
        Assert.Equal(UserFileAction.Refreshed, action);
    }

    [Fact]
    public void User_edited_json_is_merged_keeping_user_keys_and_adding_managed()
    {
        const string user = "{ \"permissions\": { \"allow\": [\"Bash\"] }, \"my\": \"edit\" }";
        var (action, content) = UserFilePolicy.Decide(user, Managed, isJson: true);
        Assert.Equal(UserFileAction.Merged, action);
        Assert.Contains("\"my\"", content, StringComparison.Ordinal);          // user key kept
        Assert.Contains("\"permissions\"", content, StringComparison.Ordinal); // user key kept
        Assert.Contains("$schema", content, StringComparison.Ordinal);          // managed key added
    }

    [Fact]
    public void User_value_wins_on_a_key_conflict()
    {
        const string managed = "{ \"x\": \"managed\" }";
        const string user = "{ \"x\": \"user\" }";
        var (action, content) = UserFilePolicy.Decide(user, managed, isJson: true);
        Assert.Equal(UserFileAction.Merged, action);
        Assert.Contains("\"user\"", content, StringComparison.Ordinal);
        Assert.DoesNotContain("\"managed\"", content, StringComparison.Ordinal);
    }

    [Fact]
    public void Non_json_user_edit_is_pending_consent()
    {
        var (action, content) = UserFilePolicy.Decide("user wrote prose here", "managed text", isJson: false);
        Assert.Equal(UserFileAction.PendingConsent, action);
        Assert.Equal("user wrote prose here", content); // user content kept untouched
    }

    [Fact]
    public void Invalid_json_is_pending_consent_never_discarded()
    {
        var (action, content) = UserFilePolicy.Decide("{ not valid json", Managed, isJson: true);
        Assert.Equal(UserFileAction.PendingConsent, action);
        Assert.Equal("{ not valid json", content);
    }
}
