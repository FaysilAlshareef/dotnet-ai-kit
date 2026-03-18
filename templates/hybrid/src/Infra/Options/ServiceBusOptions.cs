using System.ComponentModel.DataAnnotations;

namespace {{ Company }}.{{ Domain }}.Commands.Infra.Options;

public class ServiceBusOptions
{
    [Required]
    public string ConnectionString { get; set; } = default!;

    [Required]
    public string TopicName { get; set; } = default!;
}
