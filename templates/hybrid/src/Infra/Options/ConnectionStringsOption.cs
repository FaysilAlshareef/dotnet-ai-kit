using System.ComponentModel.DataAnnotations;

namespace {{ Company }}.{{ Domain }}.Commands.Infra.Options;

public class ConnectionStringsOption
{
    [Required]
    public string DefaultConnection { get; set; } = default!;
}
