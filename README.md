# tune-prompt.py

## Overview

`tune-prompt.py` is an interactive command-line tool for prompt engineering and tuning with Ollama models. It helps you refine prompt templates, fill in variables, and improve prompt quality through model responses and your feedback.

## Features
- Interactive prompt template editing and variable filling
- Automatic detection of missing variables
- Integration with Ollama models (default: gemma3:1b)
- Adjustable model parameters (temperature, top_p, num_threads)
- Iterative prompt revision based on user-specified problems
- Save/load prompt templates and variable sets

## Requirements
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
python tune-prompt.py --prompt <prompt_file> --vars <vars_file> --model <model_name>
```


All arguments are optional:
- `--prompt <file>`: Path to the prompt template file (default: `prompt.txt`)
- `--vars <file>`: Path to the variables JSON file (default: `vars.json`)
- `--model <name>`: Name of the Ollama model to use

Example:

```bash
python tune-prompt.py --prompt sample_prompt.txt --vars sample_vars.txt --model gemma3:1b
```

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