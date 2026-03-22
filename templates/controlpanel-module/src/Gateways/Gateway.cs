namespace {{ Company }}.ControlPanel.{{ Domain }}.Gateways;

public class Gateway(HttpClient httpClient)
{
    // Nested management classes, lazy initialized per domain area
    // private {{ Domain }}Management? _{{ domain }}Management;
    // public {{ Domain }}Management {{ Domain }} => _{{ domain }}Management ??= new(httpClient);
}
