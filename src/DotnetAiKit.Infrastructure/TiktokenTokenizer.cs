using DotnetAiKit.Application.Ports;
using LibTokenizers = Microsoft.ML.Tokenizers;

namespace DotnetAiKit.Infrastructure;

/// <summary>Counts tokens with the cl100k_base encoding (embedded data; no network) for budget checks.</summary>
public sealed class TiktokenTokenizer : ITokenizer
{
    private static readonly LibTokenizers.TiktokenTokenizer Inner =
        LibTokenizers.TiktokenTokenizer.CreateForEncoding("cl100k_base");

    public int CountTokens(string text) =>
        string.IsNullOrEmpty(text) ? 0 : Inner.CountTokens(text);
}
