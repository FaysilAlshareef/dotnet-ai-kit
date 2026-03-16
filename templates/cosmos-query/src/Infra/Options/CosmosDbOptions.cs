using System.ComponentModel.DataAnnotations;

namespace {{ Company }}.{{ Domain }}.Queries.Infra.Options;

public class CosmosDbOptions
{
    [Required]
    public string AccountEndpoint { get; set; } = default!;

    public string? AuthKey { get; set; }

    public bool UseServicePrincipal { get; set; }

    [Required]
    public string DatabaseName { get; set; } = default!;
}
