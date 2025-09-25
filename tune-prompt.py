
import json
import os
import ollama
import sqlite3

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

def detect_prompt_type(prompt_template, model='gemma3:1b', temperature=0.2, top_p=0.9, num_threads=4):
    """
    Use LLM to infer the task type from the template prompt.
    """
    type_query = (
        "Analyze the following prompt template and label its task type in less than 3 words (e.g., summarization, classification, extraction of JIRA, translation to Japanese, short storygeneration, etc.).\n"
        "Output ONLY the type, no explanation or extra text.\n"
        f"PROMPT TEMPLATE:\n{prompt_template}\n"
    )
    result = query(type_query, model=model, temperature=temperature, top_p=top_p, num_threads=num_threads)
    return result.strip().split()[0].lower()

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

def init_db(db_path='tune_prompt.db'):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS prompt_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session INTEGER,
            type TEXT,
            model TEXT,
            prompt TEXT,
            result TEXT,
            feedback TEXT,
            accepted INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS session_summary (
            type TEXT PRIMARY KEY,
            summary TEXT
        )
    ''')
    conn.commit()
    return conn

def save_to_db(conn, session, prompt_type, model, prompt, result, feedback, accepted):
    c = conn.cursor()
    c.execute('INSERT INTO prompt_history (session, type, model, prompt, result, feedback, accepted) VALUES (?, ?, ?, ?, ?, ?, ?)', (session, prompt_type, model, prompt, result, feedback, accepted))
    conn.commit()

def get_session_summary(conn, prompt_type):
    c = conn.cursor()
    c.execute('SELECT summary FROM session_summary WHERE type=?', (prompt_type,))
    row = c.fetchone()
    return row[0] if row and row[0] else ""

def save_session_summary(conn, prompt_type, summary):
    c = conn.cursor()
    c.execute('''
        INSERT INTO session_summary (type, summary) VALUES (?, ?)
        ON CONFLICT(type) DO UPDATE SET summary=excluded.summary
    ''', (prompt_type, summary))
    conn.commit()

def prompt_tuning_loop(
    prompt_template_path=None,
    variables_path=None,
    model='gemma3:1b',
    temperature=0.6,
    top_p=0.9,
    num_threads=21,
    db_path='tune_prompt.db',
    learn=False
):
    """
    Full interactive prompt tuning with:
    - loading/saving prompt template and variables
    - automatic variable input
    - advanced formatting error handling
    """
    if learn:
        # Initialize SQLite DB
        conn = init_db(db_path)
        # Session number: auto-increment integer per script run
        c = conn.cursor()
        c.execute('SELECT MAX(session) FROM prompt_history')
        row = c.fetchone()
        session = (row[0] + 1) if row and row[0] is not None else 1

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

    # Detect prompt type using LLM
    if learn:
        prompt_type = detect_prompt_type(current_prompt, model=model)
        print(f"Detected prompt type: {prompt_type}")

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
            print("Prompt rejected due to formatting error.")
            break

        print("\n--- Current Prompt ---\n")
        print(filled_prompt)

        response = query(filled_prompt, model=model, temperature=temperature, top_p=top_p, num_threads=num_threads)
        print("\n--- Model Response ---\n")
        print(response)

        print("\nAny problems to fix? (Enter problem description or press Enter to finish)")
        problems = input().strip()

        # If user provided feedback, consider prompt rejected and skip accept question
        if problems:
            accepted = 0
            if learn:
                # Get session summary for tuning
                session_summary = get_session_summary(conn, prompt_type)
                print("\nRevising prompt now...")
            else:
                session_summary = ""
            revision_query = f'''
You are a prompt engineering assistant. Your task is to revise the following prompt template to address the user's specified problems.
Do not simply repeat the original prompt.
CURRENT PROMPT:
{current_prompt}
END OF CURRENT PROMPT.

PROBLEMS:
{problems}
{session_summary}
END OF PROBLEMS.

Output ONLY the revised prompt template in f-string format.
Do not add any greeting, explanation, suggestions or extra text.
No code blocks like ```python or f""".
            '''
            revised_prompt = query(revision_query, model=model, temperature=temperature, top_p=top_p, num_threads=num_threads).strip()
            current_prompt = revised_prompt

            print(revision_query)

            print("\nTrying this prompt:\n")
            print(current_prompt)
            if learn:
                # Save to SQLite DB
                save_to_db(conn, session, prompt_type, model, filled_prompt, response, problems, accepted=0)
        else:
            # Ask if user accepts the prompt
            accept_choice = input("Do you accept this prompt? (y/n): ").strip().lower()
            accepted = 1 if accept_choice == 'y' else 0
            if learn:
                save_to_db(conn, session, prompt_type, model, filled_prompt, response, problems, accepted)

            # If accepted, summarize preferences/thoughts to check
            prompt_file = input("Enter filename to save prompt template (e.g., prompt.txt), or press Enter to skip: ").strip()
            if prompt_file:
                with open(prompt_file, 'w', encoding='utf-8') as f:
                    f.write(current_prompt)
                print(f"Prompt saved to {prompt_file}")
            else:
                print("Skipping prompt template save.")

            vars_file = input("Enter filename to save variables JSON (e.g., vars.json), or press Enter to skip: ").strip()
            if vars_file:
                save_to_file(variables, vars_file)
            else:
                print("Skipping variables save.")

            if learn:
                prev_summary = get_session_summary(conn, prompt_type)
                # Gather all feedbacks from the current session
                c.execute('SELECT feedback FROM prompt_history WHERE session=? AND feedback IS NOT NULL AND feedback != ""', (session,))
                feedbacks = [row[0] for row in c.fetchall()]
                feedback_summary = ""
                # Merge previous summary with new feedbacks only if previous summary is not empty
                if prev_summary:
                    summary_query = (
                        f"Summarize the following feedbacks and previous summary for prompt type '{prompt_type}' into a concise summary for future improvements:\n"
                        f"PREVIOUS SUMMARY:\n{prev_summary}\nEND OF PREVIOUS SUMMARY.\n"
                        f"FEEDBACKS:\n" + "\n".join(feedbacks) + "\nEND OF FEEDBACKS."
                        "\nNo greetings or extra text, just the summary."
                    )
                else:
                    summary_query = (
                        f"Summarize the following problems for prompt type '{prompt_type}' into a very concise summary for future improvements.\n"
                        f"PROBLEMS:\n" + "\n".join(feedbacks) + "\nEND OF PROBLEMS."
                        "\nNo greetings or extra text, just the summary."
                    )
                print(f"\n--- Tuning Preferences Summary ---\n")
                feedback_summary = query(summary_query, model=model, temperature=temperature, top_p=top_p, num_threads=num_threads).strip()
                print(feedback_summary)
                save_session_summary(conn, prompt_type, feedback_summary)
            print("Exiting tuning loop.")
            break


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
    parser.add_argument('--learn', action='store_true', help='Enable learning mode, which saves your feedback and preferences to an external database and uses them to improve future prompts.')
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

    prompt_tuning_loop(prompt_template_path=prompt_path, variables_path=variables_path, model=model_name, learn=args.learn)
