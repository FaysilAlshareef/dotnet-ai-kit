using DotnetAiKit.Application.Ports;
using DotnetAiKit.Core.Artifacts;

namespace DotnetAiKit.Hosts;

/// <summary>
/// Emits a skill's bundled resources alongside its projected <c>SKILL.md</c>, one <see cref="ProjectedFile"/>
/// per resource at <c>&lt;hostSkillsPrefix&gt;/&lt;skill&gt;/&lt;relativePath&gt;</c> (e.g.
/// <c>claude/skills/add-aggregate/examples/Order.cs</c>). Shared by every host projector that gives a skill
/// its own directory, so resources reach that assistant's skill tree (FR-022-04). Pure — content comes from
/// the model (the repository loaded it), so the orphan-cleanup in <c>generate</c> never deletes resources.
/// </summary>
internal static class SkillResourceProjection
{
    public static IEnumerable<ProjectedFile> Emit(Skill skill, string hostSkillsPrefix)
    {
        foreach (var resource in skill.Resources.All())
            yield return new ProjectedFile(
                $"{hostSkillsPrefix}/{skill.Name.Value}/{resource.RelativePath}", resource.Content);
    }
}
