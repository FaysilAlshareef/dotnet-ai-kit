using DotnetAiKit.Core;
using DotnetAiKit.Core.Values;
using Xunit;

namespace DotnetAiKit.Core.Tests;

public class ValueObjectTests
{
    [Theory]
    [InlineData("query-entity")]
    [InlineData("add-aggregate")]
    [InlineData("a")]
    [InlineData("openapi-scalar")]
    public void ArtifactName_accepts_valid_kebab(string raw)
    {
        var name = ArtifactName.From(raw);
        Assert.Equal(raw, name.Value);
    }

    [Theory]
    [InlineData("")]
    [InlineData("Has-Caps")]
    [InlineData("-leading")]
    [InlineData("trailing-")]
    [InlineData("double--hyphen")]
    [InlineData("under_score")]
    [InlineData("with space")]
    public void ArtifactName_rejects_invalid(string raw) =>
        Assert.Throws<DomainException>(() => ArtifactName.From(raw));

    [Fact]
    public void ArtifactName_rejects_over_64_chars() =>
        Assert.Throws<DomainException>(() => ArtifactName.From(new string('a', 65)));

    [Fact]
    public void ArtifactName_equality_is_by_value()
    {
        Assert.Equal(ArtifactName.From("query-entity"), ArtifactName.From("query-entity"));
        Assert.NotEqual(ArtifactName.From("a"), ArtifactName.From("b"));
    }

    [Fact]
    public void Description_rejects_empty_and_too_long()
    {
        Assert.Throws<DomainException>(() => Description.From("  "));
        Assert.Throws<DomainException>(() => Description.From(new string('x', Description.MaxLength + 1)));
    }

    [Fact]
    public void Glob_normalizes_backslashes()
    {
        var g = Glob.From("src\\Domain\\**\\*.cs");
        Assert.Equal("src/Domain/**/*.cs", g.Value);
    }

    [Theory]
    [InlineData("1.0.0", 1, 0, 0)]
    [InlineData("2.13.4", 2, 13, 4)]
    public void SemVer_parses(string raw, int maj, int min, int patch)
    {
        var v = SemVer.Parse(raw);
        Assert.Equal((maj, min, patch), (v.Major, v.Minor, v.Patch));
    }

    [Theory]
    [InlineData("1.0")]
    [InlineData("x.y.z")]
    [InlineData("1.0.0.0")]
    public void SemVer_rejects_invalid(string raw) =>
        Assert.Throws<DomainException>(() => SemVer.Parse(raw));

    [Fact]
    public void SemVer_orders_correctly() =>
        Assert.True(SemVer.Parse("1.2.0") > SemVer.Parse("1.1.9"));

    [Fact]
    public void TokenBudget_is_within_or_overflows()
    {
        Assert.True(TokenBudget.Of(90, 100).IsWithin);
        var over = TokenBudget.Of(120, 100);
        Assert.False(over.IsWithin);
        Assert.Equal(20, over.Overflow);
    }

    [Theory]
    [InlineData("claude", HostName.Claude)]
    [InlineData("COPILOT", HostName.Copilot)]
    public void HostName_parses_case_insensitively(string raw, HostName expected) =>
        Assert.Equal(expected, HostNames.Parse(raw));

    [Fact]
    public void HostName_rejects_unknown() =>
        Assert.Throws<DomainException>(() => HostNames.Parse("windsurf"));

    [Fact]
    public void HostName_slugs_round_trip()
    {
        foreach (var h in HostNames.All)
            Assert.Equal(h, HostNames.Parse(h.ToSlug()));
    }
}
