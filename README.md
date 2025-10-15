# tune-prompt.py

## Overview
`tune-prompt.py` is an interactive CLI tool for prompt engineering with Ollama models. Iteratively refine prompts through model responses and feedback, with database support for saving/loading templates and learning from tuning history.

Use https://github.com/alroborol/log-prompt alongside to get a minimal PromptOps system.

## Features
- Iterative prompt revision based on feedback
- Save/load templates and variables (file or database)
- Interactive template editing and variable filling
- Ollama model integration
- Learning mode: saves tuning history and builds personalized preferences
- log-prompt database support with tagging, search, and reuse (log-prompt is here: https://github.com/alroborol/log-prompt)

![Demo of tune-prompt.py in action](demo.gif)

## Dependency
- Python 3.8+
- [Ollama Python package](https://pypi.org/project/ollama/)

```bash
pip install ollama
```

## Usage

**General Workflow:** (Logging prompts using [log-prompt](https://github.com/alroborol/log-prompt)) → Load/enter prompts → Fill variables → View response → Give feedback → Revise → Repeat

**Interactive Mode:**
```bash
python tune-prompt.py
```

**File Mode:**
```bash
python tune-prompt.py --prompt sample_prompt.txt --vars sample_vars.txt [--learn]
```

**Database Mode:**

Open a log-prompt database and tune the prompts interactively(with `--random-vars` random variables are picked to fill the prompts):
```bash
# Random prompt selection
python tune-prompt.py --prompts-db example.db --random-vars [--learn]
```


Other examples for starters:
```bash
# List all prompts
python tune-prompt.py --list-prompts

# Load by ID or tag
python tune-prompt.py --prompt-id 1 --model gemma3:1b
python tune-prompt.py --prompt-tag "summarization" --model gemma3:1b
```

## More Examples

**Create and save:**
```bash
python tune-prompt.py --model gemma3:1b
# Save to database with tag "article-summary"
```

**Reuse saved prompt:**
```bash
python tune-prompt.py --list-prompts
python tune-prompt.py --prompt-id 1 --model gemma3:1b
```

**Work with tags:**
```bash
python tune-prompt.py --prompt-tag "translation" --model gemma3:1b
```

**Custom database:**
```bash
python tune-prompt.py --prompts-db my_prompts.db --db my_history.db --model gemma3:1b --learn
```

**Random variables (variety across same tag):**
```bash
python tune-prompt.py --prompt-tag "translation" --random-vars --model gemma3:1b
```

**Combine workflows:**
```bash
echo "Translate {text} to {language}" > translation_prompt.txt
echo '{"text": "Hello", "language": "Spanish"}' > vars.json
python tune-prompt.py --prompt translation_prompt.txt --vars vars.json --model gemma3:1b
```

## Arguments
All optional:
- `--prompt <file>`: Prompt template file (default: `prompt.txt`)
- `--vars <file>`: Variables JSON file (default: `vars.json`)
- `--model <name>`: Ollama model name
- `--learn`: Enable learning mode (saves feedback to improve future prompts)
- `--db <file>`: Learning/history database (default: `tune_prompt.db`)
- `--prompts-db <file>`: Prompts database (default: `prompts.db`, **must be created by external apps**)
- `--prompt-id <id>`: Load prompt by ID
- `--prompt-tag <tag>`: Load prompt by tag
- `--random-vars`: Randomly select from multiple prompts with same tag
- `--list-prompts`: List all stored prompts

**Note:** Two databases are used:
- `prompts.db` - Stores prompts/variables (**created by external tools like [log-prompt](https://github.com/alroborol/log-prompt)**)
- `tune_prompt.db` - Stores learning history (auto-created with `--learn`)

## Database Schema

**prompt_history** - Tracks prompts, results, feedback per session

| Column    | Type     | Description                          |
|-----------|----------|--------------------------------------|
| id        | INTEGER  | Primary key                          |
| session   | INTEGER  | Session number                       |
| type      | TEXT     | Prompt type                          |
| model     | TEXT     | Model name                           |
| prompt    | TEXT     | Filled prompt template               |
| result    | TEXT     | Model response                       |
| feedback  | TEXT     | User feedback                        |
| accepted  | INTEGER  | 1=accepted, 0=revised                |
| timestamp | DATETIME | Creation time                        |

**session_summary** - Stores preferences per prompt type

| Column  | Type | Description                    |
|---------|------|--------------------------------|
| type    | TEXT | Prompt type (primary key)      |
| summary | TEXT | Merged feedback/preferences    |

Database auto-created in script directory as `tune_prompt.db`.

## Tips
- Use descriptive tags: `email-summary`, `code-review-python`
- Version prompts: `summarize-v1`, `summarize-v2`
- Backup databases: `cp prompts.db backups/prompts_$(date +%Y%m%d).db`
- Search: `python tune-prompt.py --list-prompts | grep "summary"`
