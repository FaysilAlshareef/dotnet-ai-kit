using System.ComponentModel.DataAnnotations;

namespace {{ Company }}.Gateways.{{ Domain }}.Management.Options;

public class AuthOptions
{
    [Required]
    public string Authority { get; set; } = default!;

    [Required]
    public string Audience { get; set; } = default!;
}
