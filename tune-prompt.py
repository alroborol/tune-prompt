import json
import os
import ollama

def query(prompt_text, model='gemma3:1b', temperature=0.6, top_p=0.9, num_threads=21):
    """
    Query the ollama model with prompt and options.
    """
    options = ollama.Options(
        temperature=temperature,
        top_p=top_p,
        num_thread=num_threads
    )
    print("Ollama is running. Please wait, this may take some time...")
    response = ollama.generate(model=model, options=options, prompt=prompt_text)
    return response['response']

def input_missing_vars(template, variables):
    """
    Given a prompt template and existing variables dict,
    find missing keys and prompt user to input them.
    """
    import string

    # Extract placeholders from the template
    formatter = string.Formatter()
    keys = {fname for _, fname, _, _ in formatter.parse(template) if fname}

    missing = keys - variables.keys()
    if missing:
        print(f"Missing variables detected: {missing}")
    for key in missing:
        val = input(f"Please provide a value for variable '{key}': ")
        variables[key] = val
    return variables

def save_to_file(data, filepath):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    print(f"Saved to {filepath}")

def load_from_file(filepath):
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return None
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if not content:
                print(f"Warning: {filepath} is empty. Using empty variables.")
                return {}
            data = json.loads(content)
        print(f"Loaded from {filepath}")
        return data
    except json.JSONDecodeError as e:
        print(f"Warning: Could not decode JSON in {filepath}: {e}. Using empty variables.")
        return {}

def prompt_tuning_loop(
    prompt_template_path=None,
    variables_path=None,
    model='gemma3:1b',
    temperature=0.6,
    top_p=0.9,
    num_threads=21
):
    """
    Full interactive prompt tuning with:
    - loading/saving prompt template and variables
    - automatic variable input
    - advanced formatting error handling
    """
    # Load prompt template
    if prompt_template_path and os.path.exists(prompt_template_path):
        with open(prompt_template_path, 'r', encoding='utf-8') as f:
            current_prompt = f.read()
        print(f"Prompt template loaded from {prompt_template_path}")
    else:
        print("Please input the prompt template (use {var} for variables). End with a blank line:")
        lines = []
        while True:
            line = input()
            if line.strip() == '':
                break
            lines.append(line)
        current_prompt = '\n'.join(lines)

    # Load variables dict
    if variables_path and os.path.exists(variables_path):
        variables = load_from_file(variables_path)
        if variables is None:
            variables = {}
    else:
        variables = {}

    # Ensure all variables are filled
    variables = input_missing_vars(current_prompt, variables)

    while True:
        # Format prompt safely
        try:
            filled_prompt = current_prompt.format(**variables)
        except KeyError as e:
            print(f"ERROR: Missing variable '{e.args[0]}' during formatting.")
            val = input(f"Please provide a value for '{e.args[0]}': ")
            variables[e.args[0]] = val
            continue
        except Exception as e:
            print(f"Unexpected formatting error: {e}")
            print("You may want to edit the prompt template.")
            choice = input("Edit prompt? (y/n): ").strip().lower()
            if choice == 'y':
                print("Enter new prompt template. End with blank line:")
                lines = []
                while True:
                    line = input()
                    if line.strip() == '':
                        break
                    lines.append(line)
                current_prompt = '\n'.join(lines)
                variables = input_missing_vars(current_prompt, variables)
                continue
            else:
                print("Exiting due to error.")
                break

        print("\n--- Current Prompt ---\n")
        print(filled_prompt)

        response = query(filled_prompt, model=model, temperature=temperature, top_p=top_p, num_threads=num_threads)
        print("\n--- Model Response ---\n")
        print(response)

        print("\nAny problems to fix? (Enter problem description or press Enter to finish)")
        problems = input().strip()
        if not problems:
            print("No problems reported. Exiting tuning loop.")
            break

        print("\nRevising prompt now...")
        revision_query = f'''
Improve the following prompt for {model}. User specified some problems with the current prompt in f-string.
Output ONLY the revised prompt.
CURRENT PROMPT
{current_prompt}
END OF CURRENT PROMPT

PROBLEMS
{problems}
END OF PROBLEMS
Output only the revised prompt.
Keep f-string format. Do not add any greeting or END OF PROMPT-like text.
'''
        revised_prompt = query(revision_query, model=model, temperature=temperature, top_p=top_p, num_threads=num_threads).strip()
        current_prompt = revised_prompt

        # Ask if user wants to update variables (maybe new placeholders appeared)
        variables = input_missing_vars(current_prompt, variables)

        print("\nTrying this prompt:\n")
        print(current_prompt)

        # Save current prompt and variables to files
        save_choice = input("\nSave current prompt and variables? (y/n): ").strip().lower()
        if save_choice == 'y':
            prompt_file = input("Enter filename to save prompt template (e.g., prompt.txt): ").strip()
            with open(prompt_file, 'w', encoding='utf-8') as f:
                f.write(current_prompt)
            print(f"Prompt saved to {prompt_file}")

            vars_file = input("Enter filename to save variables JSON (e.g., vars.json): ").strip()
            save_to_file(variables, vars_file)


import sys

if __name__ == "__main__":
    # Default filenames
    default_prompt_file = 'prompt.txt'
    default_vars_file = 'vars.json'

    # Parse command-line arguments by flag
    # Usage: script.py --prompt <file> --vars <file> --model <name>
    import argparse
    parser = argparse.ArgumentParser(description="Prompt tuning script")
    parser.add_argument('--prompt', type=str, default=default_prompt_file, help='Prompt template file')
    parser.add_argument('--vars', type=str, default=default_vars_file, help='Variables file (JSON)')
    parser.add_argument('--model', type=str, default=None, help='Model name')
    args = parser.parse_args()

    prompt_file = args.prompt
    vars_file = args.vars
    model_name = args.model

    # If no model is passed, list available models and ask user to pick
    if not model_name:
        print("No model name provided. Listing available models:")
        try:
            models = ollama.list()['models']
            if not models:
                print("No models found in ollama.")
                exit(1)
            print("Available models:")
            # Try both 'name' and 'model' keys for compatibility
            def get_model_name(m):
                return m.get('name') or m.get('model') or str(m)
            for idx, m in enumerate(models):
                print(f"  [{idx+1}] {get_model_name(m)}")
            while True:
                choice = input("Pick a model by number: ").strip()
                if not choice.isdigit() or int(choice) < 1 or int(choice) > len(models):
                    print("Invalid choice. Please enter a valid number.")
                else:
                    model_name = get_model_name(models[int(choice)-1])
                    break
        except Exception as e:
            print(f"Error listing models: {e}")
            exit(1)

    prompt_path = None
    variables_path = None

    if os.path.exists(prompt_file):
        print(f"Found prompt template file: {prompt_file}")
        prompt_path = prompt_file
    else:
        print(f"No prompt template file '{prompt_file}' found.")
        print("You can create one to save your prompt templates for re-use.")

    if os.path.exists(vars_file):
        print(f"Found variables file: {vars_file}")
        variables_path = vars_file
    else:
        print(f"No variables file '{vars_file}' found.")
        print("You can create one to save your prompt variables for re-use.")

    prompt_tuning_loop(prompt_template_path=prompt_path, variables_path=variables_path, model=model_name)
