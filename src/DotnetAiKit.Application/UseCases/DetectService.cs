using DotnetAiKit.Application.Ports;
using DotnetAiKit.Core.Project;

namespace DotnetAiKit.Application.UseCases;

/// <summary>Detects architecture, .NET version, and the path map for a target solution.</summary>
public sealed class DetectService(IDetectionProvider detector)
{
    public ProjectMetadata Run(string projectRoot) => detector.Detect(projectRoot);
}
