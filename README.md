# tune-prompt.py

## Overview

`tune-prompt.py` is an interactive command-line tool for prompt engineering and tuning with Ollama models. It helps you refine prompt templates, fill in variables, and improve prompt quality through model responses and your feedback.

## Features
- Iterative prompt revision based on user-specified problems
- Save/load prompt templates and variable sets
- Interactive prompt template editing and variable filling
- Integration with Ollama models
- Automatically saves your tuning history and creates personalized preferences to help you evaluate and improve future prompts (available when learn mode is enabled)

![Demo of tune-prompt.py in action](demo.gif)


## Dependency
- Python 3.8+
- [Ollama Python package](https://pypi.org/project/ollama/)

Install dependencies:
```bash
pip install ollama
```

## Usage

### Interactive Mode

```bash
python tune-prompt.py
```

Follow the prompts to enter your template and variables, choose a model, review the model's responses, and iteratively improve your prompt.

### Command-Line Usage


You can run `tune-prompt.py` with arguments in any order using flags:

```bash
python tune-prompt.py --prompt <prompt_file> --vars <vars_file> --model <model_name> [--learn]
```

All arguments are optional:
- `--prompt <file>`: Path to the prompt template file (default: `prompt.txt`)
- `--vars <file>`: Path to the variables JSON file (default: `vars.json`)
- `--model <name>`: Name of the Ollama model to use
- `--learn`: Enable learning mode, which saves your feedback and preferences to an external database and uses them to improve future prompts.

Example (with preferences learning):

```bash
python tune-prompt.py --prompt sample_prompt.txt --vars sample_vars.txt --model gemma3:1b --learn
```

This will:
- Load your prompt and variables
- Use the specified model
- After each model response, ask for feedback/problems
- Revise the prompt using your feedback
- Save all feedback, prompt history, and session summaries in `./tune_prompt.db`

If you do not provide `--model`, the script will list available models and prompt you to select one interactively.


When a model query is running, you will see:
```
Ollama is running. Please wait, this may take some time...
```

- `sample_prompt.txt`: Example prompt template
- `sample_vars.txt`: Example variables

If you don't provide files, you'll be prompted to enter the template and variables interactively.

### Workflow
1. Load or enter a prompt template (use `{var}` for variables)
2. Fill in any missing variables interactively
3. View the model's response
4. Describe any problems or issues with the prompt
5. The tool will revise the prompt using the model
6. Repeat until you are satisfied

## Sample Files

- `sample_prompt.txt`: Example prompt for testing
- `sample_vars.txt`: Example variables for the prompt


## Saving & Loading
- You can save prompts and variables to files for reuse.
- Use the same filenames to reload previous sessions.
- All feedback and session summaries are stored in `tune_prompt.db` for future reference and prompt improvement.

## Database Structure

All feedback and session data are stored in a local SQLite database file named `tune_prompt.db`.

### Tables

#### prompt_history
Tracks every prompt, result, feedback, and acceptance for each session.

| Column    | Type      | Description                                      |
|-----------|-----------|-------------------------------------------------|
| id        | INTEGER   | Auto-increment primary key                       |
| session   | INTEGER   | Session number                                   |
| type      | TEXT      | Detected or specified prompt type                |
| model     | TEXT      | Model name used                                  |
| prompt    | TEXT      | Prompt template (after variable filling)         |
| result    | TEXT      | Model response                                   |
| feedback  | TEXT      | User feedback/problems                           |
| accepted  | INTEGER   | 1 if accepted, 0 if revised                      |
| timestamp | DATETIME  | When the entry was created                       |

#### session_summary
Stores a summary of preferences and feedback for each prompt type.

| Column    | Type      | Description                                      |
|-----------|-----------|-------------------------------------------------|
| type      | TEXT      | Prompt type (primary key)                        |
| summary   | TEXT      | Merged summary of feedback/preferences           |


All feedback, prompt history, and session summaries are automatically saved in a local SQLite database file named `tune_prompt.db` in the same directory as the script. You do not need to configure anything; the database is created and updated automatically.