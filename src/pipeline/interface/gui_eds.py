# pipeline/interfaces/gui_eds.py

import FreeSimpleGUI as sg
from typer import BadParameter
import json
from pathlib import Path
from pipeline.core import eds as eds_core

# Set theme for a slightly better look
sg.theme('DarkGrey15') 


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

# --- Status Bar Helper Function ---
def update_status(window, message, color='white'):
    """Updates the status bar text and color."""
    # Use an alias to the element for cleaner code
    window['STATUS_BAR'].update(message, text_color=color)
    window.refresh()

def launch_fsg():
    """Launches the FreeSimpleGUI interface for EDS Trend."""
    
    # Load history for the dropdown list
    idcs_history = load_history()

    # Define the layout
    layout = [
        [sg.Text("EDS Trend", font=("Helvetica", 16))],
        [sg.HorizontalSeparator()],
        
        #[sg.Text("Ovation Sensor IDCS (e.g., M100FI M310LI FI8001). Separate with spaces. Leave empty to use configured defaults.", size=(70, 2))],
        #[sg.InputText(key="idcs_list", size=(70, 1))],
        #[sg.Checkbox("Use Configured Default IDCS", key="default_idcs", default=False)],
        
        # *** MODIFIED SECTION: Changed sg.InputText to sg.Combo ***
        [sg.Text("Ovation Sensor IDCS (e.g., M100FI M310LI FI8001). Separate with spaces. Type a new query or select from history.", size=(70, 2))],
        [sg.Combo(
            values=idcs_history,                 # The list of historical queries
            default_value=idcs_history[0] if idcs_history else '', # Default to the last query
            size=(70, 1),
            key="idcs_list",
            enable_events=False,                 # Do not trigger events when an item is selected
            readonly=False                       # Allows typing new entries
        )],
        [sg.Checkbox("Use Configured Default IDCS", key="default_idcs", default=False)],
        # *** END MODIFIED SECTION ***
        
        [sg.HorizontalSeparator()],
        
        [sg.Text("Time Range (Start/End/Days)", font=("Helvetica", 12))],
        [sg.Text("Days:", size=(10, 1)), sg.InputText(key="days", size=(15, 1)), 
         sg.Text("Start Time:", size=(10, 1)), sg.InputText(key="starttime", size=(25, 1)), 
         sg.Text("End Time:", size=(10, 1)), sg.InputText(key="endtime", size=(25, 1))],
        
        [sg.HorizontalSeparator()],

        [sg.Text("Plot Options", font=("Helvetica", 12))],
        [sg.Text("Time Step/Datapoints (Leave empty for automatic):", size=(40, 1))],
        [sg.Text("Seconds Between Points:", size=(20, 1)), sg.InputText(key="seconds_between_points", size=(10, 1)),
         sg.Text(" OR "),
         sg.Text("Datapoint Count:", size=(15, 1)), sg.InputText(key="datapoint_count", size=(10, 1))],
        
        [sg.HorizontalSeparator()],
        
        [sg.Radio("Web-Based Plot (Plotly)", group_id= "plot_environment", key="force_webplot", default=True, tooltip="Uses Plotly/browser. Recommended for most users."),
         sg.Radio("Matplotlib Plot (Local)", group_id= "plot_environment", key="force_matplotlib", default=False, tooltip="Uses Matplotlib. Requires a local display environment.")],
        
        [sg.HorizontalSeparator()],
        
        [sg.Button("Fetch & Plot Trend", key="OK"), sg.Button("Cancel")]
    ]

    window = sg.Window("EDS Trend", layout, finalize=True)

    while True:
        event, values = window.read()
        
        if event == sg.WIN_CLOSED or event == "Cancel":
            break

        if event == "OK":
            # --- Input Processing ---
            # Typer Argument (idcs) is a list[str], so we need to convert the string.
            idcs_input = values["idcs_list"].strip()
            # Save the successful input to history
            if idcs_input and idcs_input != (idcs_history[0] if idcs_history else ''): # Only save if non-empty and new/different
                save_history(idcs_input)
            idcs_list = idcs_input.split() if idcs_input else None
            
            # Convert optional inputs to their correct types or None
            try:
                days = float(values["days"]) if values["days"] else None
                sec_between = int(values["seconds_between_points"]) if values["seconds_between_points"] else None
                dp_count = int(values["datapoint_count"]) if values["datapoint_count"] else None
            except ValueError:
                sg.popup_error("Invalid number entered for Days, Seconds, or Datapoint Count.")
                continue

            starttime = values["starttime"] if values["starttime"] else None
            endtime = values["endtime"] if values["endtime"] else None
            
            # Typer boolean options
            default_idcs = values["default_idcs"]
            force_webplot = values["force_webplot"]
            force_matplotlib = values["force_matplotlib"]
            
            # --- Core Logic Execution ---
            try:
                # The core function handles all the logic and error checking
                data_buffer, _ = eds_core.fetch_trend_data(
                    idcs=idcs_list, 
                    starttime=starttime, 
                    endtime=endtime, 
                    days=days, 
                    plant_name=None, # Not an option in the current GUI
                    seconds_between_points=sec_between, 
                    datapoint_count=dp_count,
                    default_idcs=default_idcs
                )
                
                if data_buffer.is_empty():
                    #sg.popup_ok("Success, but no data points were returned for the selected time range and sensors.")
                    update_status(window, "Success, but no data points were returned for the selected time range and sensors.", 'yellow')
                else:
                    # --- Plotting ---
                    update_status(window, "Data successfully fetched. Launching plot...", 'lime')
                    eds_core.plot_trend_data(data_buffer, force_webplot, force_matplotlib)
                    update_status(window, "Plot launched. Ready for new query.", 'white')
                    
            except BadParameter as e:
                # Catch the specific error raised by the core logic
                #sg.popup_error("Configuration/Input Error:", str(e).strip())
                update_status(window, f"Configuration/Input Error: {str(e).strip()}", 'red')
            except Exception as e:
                # Catch all other unexpected errors
                #sg.popup_error("An unexpected error occurred during data fetching:", str(e))
                update_status(window, f"An unexpected error occurred: {str(e)}", 'red')

    window.close()

if __name__ == "__main__":
    launch_fsg()

