# AI Legacy Code Mapper

Open-source CLI that reverse engineers legacy Laravel/PHP projects into Markdown,
Mermaid diagrams and structured JSON. The analyzer performs static analysis and
does not execute the target application.

## Output

```text
docs/generated/
├── api-map.md
├── business-flows.md
├── database-map.md
├── sequence-diagrams.md
├── risk-report.md
├── summary.md
└── analysis.json
```

## Windows Quick Start

Open PowerShell or Command Prompt and move to the mapper directory:

```powershell
git clone https://github.com/minhnguyen1108/ai-legacy-code-mapper.git
cd ai-legacy-code-mapper
```

Run the bundled example:

```powershell
.\analyze.cmd ".\examples\laravel5-support"
```

Analyze a local Laravel project:

```powershell
.\analyze.cmd "C:\projects\legacy-laravel-app"
```

Important path rules:

- Use the absolute path to the Laravel project.
- Wrap the path in double quotes, especially when it contains spaces.
- Do not add a dot before a drive path. Use `"D:\project"`, not `".D:\project"`.
- The project directory must exist and contain PHP source files.

The generated documentation is written to:

```text
<laravel-project>\docs\generated
```

Analyze a Git repository:

```powershell
.\analyze.cmd https://github.com/company/project.git
```

For Git URLs, the default output is `.\docs\generated` in the mapper workspace
because the shallow clone is temporary. Use `--output` to choose another folder.

Choose a custom output directory:

```powershell
.\analyze.cmd "C:\projects\legacy-laravel-app" --output "C:\reports\legacy-laravel-app"
```

Use OpenAI for Vietnamese business explanations:

```powershell
.\analyze.cmd "C:\projects\legacy-laravel-app" --provider openai
```

Use a local Ollama model:

```powershell
.\analyze.cmd "C:\projects\legacy-laravel-app" --provider ollama --model qwen2.5-coder:7b
```

By default, AI is disabled. Route mapping, call graphs, ERD, sequence diagrams,
static explanations and risk findings still work without an API key.

## Run Tests

Run all automated tests:

```powershell
cd ai-legacy-code-mapper
.\test.cmd
```

Expected result:

```text
Ran 3 tests
OK
```

Run an end-to-end scan without AI:

```powershell
.\analyze.cmd ".\examples\laravel5-support" --provider none
```

Python 3.11 or newer is required. The MVP uses only the Python standard library,
so no package installation is needed.

## Troubleshooting

### Project path is joined with the current directory

Incorrect:

```powershell
.\analyze.cmd ".C:\projects\legacy-laravel-app"
```

Correct:

```powershell
.\analyze.cmd "C:\projects\legacy-laravel-app"
```

### Python opens Microsoft Store

Use `.\test.cmd` and `.\analyze.cmd` instead of calling `python` directly.
These scripts select the working Python runtime automatically.

### OpenAI returns `insufficient_quota`

The static analyzer still generates all documentation. Add API billing or quota
to enable AI-generated business explanations, or use `--provider ollama`.

## Current Laravel Support

- Laravel 5 string routes: `Controller@action`
- Modern routes: `[Controller::class, 'action']`
- Route names, middleware and simple group prefixes
- Constructor dependency injection
- Controller → Service → Repository → Model calls
- Static Eloquent calls and `DB::table(...)`
- Models, `$table`, `$fillable`, Eloquent relationships
- Schema migrations, columns and foreign keys
- Rule-based findings for raw SQL, old hashes, debug calls, `env()` misuse,
  risky deserialize/eval and complex methods

## Accuracy Model

- `confirmed`: directly mapped to a source declaration.
- `inferred`: follows a Laravel convention, such as an Eloquent static method.
- `unknown`: dynamic behavior could not be resolved statically.

Laravel service-container bindings, macros, runtime-generated routes, dynamic
method calls and complex raw SQL may require manual review.

## Roadmap

1. Improve PHP AST coverage and container binding resolution.
2. Add cached OpenAI/Ollama business explanations and module summaries.
3. Add a Web UI for ZIP upload, interactive graph navigation and export.
4. Add NestJS, Spring Boot, .NET and Go Gin analyzers.
