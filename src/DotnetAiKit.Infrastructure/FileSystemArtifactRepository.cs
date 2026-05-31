using DotnetAiKit.Application.Ports;
using DotnetAiKit.Core;
using DotnetAiKit.Core.Artifacts;
using DotnetAiKit.Core.Graph;
using DotnetAiKit.Core.Manifest;
using DotnetAiKit.Core.Values;
using YamlDotNet.Serialization;

namespace DotnetAiKit.Infrastructure;

/// <summary>
/// Loads the authored <c>artifacts/</c> tree into Core models and builds the <c>ArtifactGraph</c>.
/// Artifact-shaping fields (kind, scope, paths, agent, skills, invocation, analyzer-backed,
/// routing-intents) live under the <c>metadata:</c> block. Aggregates all validation + broken-edge
/// errors instead of throwing on the first.
/// </summary>
public sealed class FileSystemArtifactRepository(IFileSystem fileSystem, IArtifactSerializer serializer)
    : IArtifactRepository
{
    private static readonly IDeserializer Yaml = new DeserializerBuilder().Build();

    public CorpusLoadResult Load(string artifactsRoot)
    {
        var errors = new List<string>();
        var skills = LoadSkills(artifactsRoot, errors);
        var agents = LoadAgents(artifactsRoot, errors);
        var rules = LoadRules(artifactsRoot, errors);
        var profiles = LoadProfiles(artifactsRoot, errors);
        var fragments = LoadSimple(Path.Combine(artifactsRoot, "fragments"), errors,
            (name, fm, body) => new Fragment { Name = name, Description = fm.Description, Body = body });
        var knowledge = LoadSimple(Path.Combine(artifactsRoot, "knowledge"), errors,
            (name, fm, body) => new KnowledgeDoc { Name = name, Description = fm.Description, Body = body });

        foreach (var artifact in Enumerable.Empty<IArtifact>()
                     .Concat(skills).Concat(agents).Concat(rules).Concat(profiles).Concat(fragments).Concat(knowledge))
            errors.AddRange(artifact.Validate());

        var graphResult = BuildGraph(skills, agents, rules, profiles, fragments, knowledge);
        errors.AddRange(graphResult.BrokenEdges);

        var manifest = LoadManifest(artifactsRoot, skills, agents, rules, errors);

        if (errors.Count > 0)
            return new CorpusLoadResult(null, errors);

        var corpus = new ArtifactCorpus
        {
            Skills = skills,
            Agents = agents,
            Rules = rules,
            Profiles = profiles,
            Fragments = fragments,
            Knowledge = knowledge,
            Manifest = manifest,
            Graph = graphResult.Graph,
        };
        return new CorpusLoadResult(corpus, []);
    }

    private List<Skill> LoadSkills(string root, List<string> errors)
    {
        var result = new List<Skill>();
        var skillsDir = Path.Combine(root, "skills");
        foreach (var file in fileSystem.EnumerateFiles(skillsDir, "SKILL.md", recursive: true))
        {
            try
            {
                var dirName = Path.GetFileName(Path.GetDirectoryName(file)!);
                var text = fileSystem.ReadAllText(file);
                var fm = serializer.ParseFrontmatter(text);
                var body = serializer.Split(text).Body;
                var meta = fm.Metadata;
                var isCommand = file.Replace('\\', '/').Contains("/skills/commands/", StringComparison.Ordinal)
                                || Meta(meta, "kind") == "command";

                // FR-022-19: the schema-version guard. The parser already populated fm.SchemaVersion
                // (top-level frontmatter, default 1.0.0); fail an out-of-range version rather than load it.
                if (!ArtifactSchema.IsSupported(fm.SchemaVersion))
                {
                    errors.Add($"skills: {file}: unsupported schema-version '{fm.SchemaVersion}' "
                        + $"(supported >={ArtifactSchema.Min} <{ArtifactSchema.MaxExclusive}; run migrate).");
                    continue;
                }

                result.Add(new Skill
                {
                    Name = ArtifactName.From(dirName),
                    Description = fm.Description,
                    Frontmatter = fm,
                    Body = body,
                    SkillKind = isCommand ? SkillKind.Command : SkillKind.Knowledge,
                    Invocation = ParseInvocation(Meta(meta, "invocation"), isCommand),
                    OwningAgent = OptionalName(Meta(meta, "agent")),
                    Paths = ParseGlobs(Meta(meta, "paths")),
                    Resources = ScanResources(Path.GetDirectoryName(file)!),
                    SchemaVersion = fm.SchemaVersion,
                });
            }
            catch (DomainException ex)
            {
                errors.Add($"skills: {file}: {ex.Message}");
            }
        }

        return result;
    }

    private List<Agent> LoadAgents(string root, List<string> errors)
    {
        var result = new List<Agent>();
        foreach (var file in fileSystem.EnumerateFiles(Path.Combine(root, "agents"), "*.md", recursive: false))
        {
            try
            {
                var text = fileSystem.ReadAllText(file);
                var fm = serializer.ParseFrontmatter(text);
                var meta = fm.Metadata;
                result.Add(new Agent
                {
                    Name = ArtifactName.From(Path.GetFileNameWithoutExtension(file)),
                    Description = fm.Description,
                    Body = serializer.Split(text).Body,
                    ReferencedSkills = ParseNames(Meta(meta, "skills")),
                    RoutingIntents = SplitList(Meta(meta, "routing-intents")),
                    HostOverrides = fm.HostExtensions,
                });
            }
            catch (DomainException ex)
            {
                errors.Add($"agents: {file}: {ex.Message}");
            }
        }

        return result;
    }

    private List<Rule> LoadRules(string root, List<string> errors)
    {
        var result = new List<Rule>();
        foreach (var (subdir, scope) in new[] { ("conventions", RuleScope.Universal), ("domain", RuleScope.Domain) })
        {
            foreach (var file in fileSystem.EnumerateFiles(Path.Combine(root, "rules", subdir), "*.md", recursive: false))
            {
                try
                {
                    var text = fileSystem.ReadAllText(file);
                    var fm = serializer.ParseFrontmatter(text);
                    var meta = fm.Metadata;
                    result.Add(new Rule
                    {
                        Name = ArtifactName.From(Path.GetFileNameWithoutExtension(file)),
                        Description = fm.Description,
                        Body = serializer.Split(text).Body,
                        Scope = scope,
                        Paths = ParseGlobs(Meta(meta, "paths")),
                        AnalyzerBacked = Meta(meta, "analyzer-backed") == "true",
                    });
                }
                catch (DomainException ex)
                {
                    errors.Add($"rules/{subdir}: {file}: {ex.Message}");
                }
            }
        }

        return result;
    }

    private List<Profile> LoadProfiles(string root, List<string> errors)
    {
        var result = new List<Profile>();
        foreach (var file in fileSystem.EnumerateFiles(Path.Combine(root, "profiles"), "*.md", recursive: true))
        {
            try
            {
                var text = fileSystem.ReadAllText(file);
                var fm = serializer.ParseFrontmatter(text);
                var meta = fm.Metadata;
                result.Add(new Profile
                {
                    Name = ArtifactName.From(Path.GetFileNameWithoutExtension(file)),
                    Description = fm.Description,
                    ConstraintBody = serializer.Split(text).Body,
                    TargetPaths = ParseGlobs(Meta(meta, "paths")),
                    AnalyzerBackedConstraints = SplitList(Meta(meta, "analyzer-backed-constraints")),
                });
            }
            catch (DomainException ex)
            {
                errors.Add($"profiles: {file}: {ex.Message}");
            }
        }

        return result;
    }

    private List<T> LoadSimple<T>(string dir, List<string> errors,
        Func<ArtifactName, Core.Frontmatter.ArtifactFrontmatter, string, T> factory)
    {
        var result = new List<T>();
        foreach (var file in fileSystem.EnumerateFiles(dir, "*.md", recursive: false))
        {
            try
            {
                var text = fileSystem.ReadAllText(file);
                var fm = serializer.ParseFrontmatter(text);
                result.Add(factory(ArtifactName.From(Path.GetFileNameWithoutExtension(file)), fm, serializer.Split(text).Body));
            }
            catch (DomainException ex)
            {
                errors.Add($"{Path.GetFileName(dir)}: {file}: {ex.Message}");
            }
        }

        return result;
    }

    private static GraphBuildResult BuildGraph(
        IEnumerable<Skill> skills, IEnumerable<Agent> agents, IEnumerable<Rule> rules,
        IEnumerable<Profile> profiles, IEnumerable<Fragment> fragments, IEnumerable<KnowledgeDoc> knowledge)
    {
        var nodes = new List<ArtifactNode>();
        foreach (var s in skills) nodes.Add(new ArtifactNode(s.Name, s.Kind));
        foreach (var a in agents) nodes.Add(new ArtifactNode(a.Name, a.Kind));
        foreach (var r in rules) nodes.Add(new ArtifactNode(r.Name, r.Kind));
        foreach (var p in profiles) nodes.Add(new ArtifactNode(p.Name, p.Kind));
        foreach (var f in fragments) nodes.Add(new ArtifactNode(f.Name, f.Kind));
        foreach (var k in knowledge) nodes.Add(new ArtifactNode(k.Name, k.Kind));

        var edges = new List<ArtifactEdge>();
        foreach (var agent in agents)
            foreach (var skillRef in agent.ReferencedSkills)
                edges.Add(new ArtifactEdge(agent.Name, skillRef, EdgeKind.OwnedBy));

        return ArtifactGraph.Build(nodes, edges);
    }

    private PluginManifest? LoadManifest(
        string root, IReadOnlyList<Skill> skills, IReadOnlyList<Agent> agents, IReadOnlyList<Rule> rules,
        List<string> errors)
    {
        var manifestFile = Path.Combine(root, "manifest.yml");
        if (!fileSystem.FileExists(manifestFile))
            return null;

        try
        {
            var map = Yaml.Deserialize<Dictionary<object, object?>>(fileSystem.ReadAllText(manifestFile))
                      ?? new Dictionary<object, object?>();
            string Get(string k) => map.TryGetValue(k, out var v) ? v?.ToString()?.Trim() ?? "" : "";
            var version = Get("version");
            return new PluginManifest
            {
                Name = Get("name").Length > 0 ? Get("name") : "dotnet-ai-kit",
                Version = version.Length > 0 ? SemVer.Parse(version) : new SemVer(2, 0, 0),
                Description = Get("description"),
                Keywords = SplitList(Get("keywords")),
                Components = new ComponentMap
                {
                    Skills = skills.Where(s => s.SkillKind == SkillKind.Knowledge).Select(s => s.Name).ToList(),
                    Agents = agents.Select(a => a.Name).ToList(),
                    Rules = rules.Select(r => r.Name).ToList(),
                    Commands = skills.Where(s => s.SkillKind == SkillKind.Command).Select(s => s.Name).ToList(),
                },
                Capabilities = DefaultCapabilityMatrix(),
            };
        }
        catch (Exception ex) when (ex is DomainException or YamlDotNet.Core.YamlException)
        {
            errors.Add($"manifest.yml: {ex.Message}");
            return null;
        }
    }

    private static HostCapabilityMatrix DefaultCapabilityMatrix() => new()
    {
        Entries =
        [
            new(HostName.Claude, "skills", CapabilityMaturity.Ga),
            new(HostName.Claude, "hooks", CapabilityMaturity.Ga),
            new(HostName.Claude, "stop-hook", CapabilityMaturity.Ga),
            new(HostName.Codex, "skills", CapabilityMaturity.Ga),
            new(HostName.Codex, "stop-hook", CapabilityMaturity.Unsupported),
            new(HostName.Cursor, "skills", CapabilityMaturity.Ga),
            new(HostName.Cursor, "stop-hook", CapabilityMaturity.Unsupported),
            new(HostName.Copilot, "skills", CapabilityMaturity.Ga),
            new(HostName.Copilot, "stop-hook", CapabilityMaturity.Unsupported),
        ],
    };

    // ---- small helpers ----
    private static string Meta(IReadOnlyDictionary<string, string> meta, string key) =>
        meta.TryGetValue(key, out var v) ? v.Trim() : string.Empty;

    private static ArtifactName? OptionalName(string value) =>
        value.Length == 0 ? null : ArtifactName.From(value);

    private static IReadOnlyList<Glob> ParseGlobs(string csv) =>
        SplitList(csv).Select(Glob.From).ToList();

    private static IReadOnlyList<ArtifactName> ParseNames(string csv) =>
        SplitList(csv).Select(ArtifactName.From).ToList();

    private static List<string> SplitList(string value) =>
        value.Split([',', ';'], StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries).ToList();

    private static InvocationPolicy ParseInvocation(string value, bool isCommand) => value switch
    {
        "disable-model-invocation" => InvocationPolicy.DisableModelInvocation,
        "user-invocable-false" => InvocationPolicy.UserInvocableFalse,
        "default" => InvocationPolicy.Default,
        _ => isCommand ? InvocationPolicy.DisableModelInvocation : InvocationPolicy.Default,
    };

    private SkillResourceSet ScanResources(string skillDir)
    {
        // Load each resource subtree with content so the (pure) projectors can emit it. Paths are
        // skill-dir-relative + forward-slashed (preserve subdirs), sorted (deterministic drift), and
        // LF-normalized (byte-stable on Windows). Text-only.
        IReadOnlyList<ResourceFile> Load(string sub)
        {
            var dir = Path.Combine(skillDir, sub);
            if (!fileSystem.DirectoryExists(dir))
                return [];
            return fileSystem.EnumerateFiles(dir, "*", recursive: true)
                .OrderBy(p => p.Replace('\\', '/'), StringComparer.Ordinal)
                .Select(p => new ResourceFile(
                    Path.GetRelativePath(skillDir, p).Replace('\\', '/'),
                    Lf(fileSystem.ReadAllText(p))))
                .ToList();
        }

        return new SkillResourceSet
        {
            Scripts = Load("scripts"),
            Examples = Load("examples"),
            References = Load("references"),
            Assets = Load("assets"),
            Evals = Load("evals"),
        };
    }

    private static string Lf(string text) => text.Replace("\r\n", "\n").Replace("\r", "\n");
}
