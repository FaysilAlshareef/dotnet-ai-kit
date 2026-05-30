namespace DotnetAiKit.Core;

/// <summary>Raised when a domain invariant is violated (parse-don't-validate failures).</summary>
public sealed class DomainException(string message) : Exception(message);
