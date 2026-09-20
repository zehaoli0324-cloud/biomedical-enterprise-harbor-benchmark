# Architecture

## Review stages

1. **Structure gate** checks required files and expected task directories.
2. **Metadata gate** parses `task.toml` and validates the fields needed to identify a task.
3. **README gate** checks that task, solution, and verification intent is documented.
4. **Trial evidence gate** checks that verifier artifacts exist. A future Harbor adapter will interpret CTRF and reward files here.
5. **LLM review** is optional and receives a read-only `TaskContext`. It can add findings, but cannot downgrade a blocker or rewrite evidence.

The final status is derived from the highest severity: any blocker means `fail`, any warning means `needs_review`, otherwise `pass`.

## Harbor alignment

The project intentionally mirrors the separation used by Harbor-style review workflows:

- machine-checkable CI gates run first;
- execution evidence is treated separately from prose quality;
- model review is a second opinion, not the source of truth;
- every finding records a check id and path so an author can act on it.

## Next milestones

- Parse Harbor CTRF, `reward.txt`, `result.json`, and trajectory artifacts.
- Add provider adapters for OpenAI-compatible and local models with structured JSON output.
- Add parallel domain/technical reviewer prompts and a bar-raiser aggregation step.
- Store immutable review snapshots for regression comparisons.

