# --- History Configuration ---
# Define a path for the history file relative to the user's home directory 
# or a configuration directory. Using a simple file in the current working directory
# or a known config folder is typical. For simplicity here, we'll use a specific
# configuration file location.
HISTORY_FILE = Path.home() / '.pipeline_eds_history.json'
MAX_HISTORY_ITEMS = 10

def load_history():
    """Loads the list of recent IDCS queries from a file."""
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    return []

def save_history(new_query: str):
    """Adds a new query to the history list and saves it."""
    history = load_history()
    
    # Clean up the new query (removes it if already present to move it to the top)
    if new_query in history:
        history.remove(new_query)
    
    # Insert at the beginning
    history.insert(0, new_query)
    
    # Truncate to maximum size
    history = history[:MAX_HISTORY_ITEMS]
    
    # Save the updated history
    try:
        with open(HISTORY_FILE, 'w') as f:
            json.dump(history, f, indent=4)
    except IOError as e:
        print(f"Warning: Could not save history to {HISTORY_FILE}. Error: {e}")
# --- End History Configuration ---
