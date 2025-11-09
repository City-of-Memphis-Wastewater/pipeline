# pipeline/interfaces/gui_eds.py


from typer import BadParameter
import json
from pathlib import Path
from pipeline.core import eds as eds_core
import pyhabitat

if not pyhabitat.on_termux() and not pyhabitat.on_ish_alpine(): 
    import FreeSimpleGUI as sg
    sg.theme('DarkGrey15') 
    import streamlit as st 

# Set theme for a slightly better look



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

def launch_fsg(web:bool=False)->None:
    """Launches the FreeSimpleGUI interface for EDS Trend."""

    if web:
        import FreeSimpleGUIWeb as sg
    else:
        import FreeSimpleGUI as sg
    # Load history for the dropdown list
    idcs_history = load_history()

    # Define the layout
    layout = [
        [sg.Text("EDS Trend", font=("Helvetica", 16))],
        #[sg.HorizontalSeparator()],
        [sg.Text('_' * 80, justification='center')],
        
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
        
        #[sg.HorizontalSeparator()],
        [sg.Text('_' * 80, justification='center')],

        [sg.Text("Time Range (Start/End/Days)", font=("Helvetica", 12))],
        [sg.Text("Days:", size=(10, 1)), sg.InputText(key="days", size=(15, 1)), 
         sg.Text("Start Time:", size=(10, 1)), sg.InputText(key="starttime", size=(25, 1)), 
         sg.Text("End Time:", size=(10, 1)), sg.InputText(key="endtime", size=(25, 1))],
        
        #[sg.HorizontalSeparator()],
        [sg.Text('_' * 80, justification='center')],

        [sg.Text("Plot Options", font=("Helvetica", 12))],
        [sg.Text("Time Step/Datapoints (Leave empty for automatic):", size=(40, 1))],
        [sg.Text("Seconds Between Points:", size=(20, 1)), sg.InputText(key="seconds_between_points", size=(10, 1)),
         sg.Text(" OR "),
         sg.Text("Datapoint Count:", size=(15, 1)), sg.InputText(key="datapoint_count", size=(10, 1))],
        
        #[sg.HorizontalSeparator()],
        [sg.Text('_' * 80, justification='center')],
        
        [sg.Radio("Web-Based Plot (Plotly)", group_id= "plot_environment", key="force_webplot", default=True, tooltip="Uses Plotly/browser. Recommended for most users."),
         sg.Radio("Matplotlib Plot (Local)", group_id= "plot_environment", key="force_matplotlib", default=False, tooltip="Uses Matplotlib. Requires a local display environment.")],
        
        #[sg.HorizontalSeparator()],
        [sg.Text('_' * 80, justification='center')],
        [sg.Button("Fetch & Plot Trend", key="OK"), sg.Button("Close")],

        [sg.Text("", size=(80, 1), key='STATUS_BAR', text_color='white', background_color='#333333')]
    ]

    if web:
        window = sg.Window("EDS Trend (Web)", layout, web_port=8080, finalize=True)
    else:
        window = sg.Window("EDS Trend", layout, finalize=True)
    update_status(window, "Ready to fetch data.")

    while True:
        event, values = window.read()
        
        if event == sg.WIN_CLOSED or event == "Close":
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
                    fig = eds_core.plot_trend_data(data_buffer, force_webplot, force_matplotlib)
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


def launch_streamlit():
    """Launches the Streamlit web interface for EDS Trend."""
    
    st.set_page_config(layout="centered", page_title="EDS Trend")
    st.title("EDS Trend")
    st.markdown("---")
    
    # --- HISTORY / IDCS INPUT ---
    idcs_history = load_history()
    
    # Use st.form for grouping inputs and handling submission cleanly
    with st.form("eds_form"):
        st.subheader("Sensor and Time Selection")
        
        # IDCS Input (Mimics Combo/History)
        idcs_input = st.text_input(
            "Ovation Sensor IDCS (e.g., M100FI). Separate with spaces.", 
            value=idcs_history[0] if idcs_history else '',
            key="idcs_list_web"
        )
        
        # Checkboxes and Time Range
        col_def, col_days, col_start, col_end = st.columns([1, 1, 1, 1])
        
        default_idcs = col_def.checkbox("Use Default IDCS")
        days_input = col_days.text_input("Days:", help="e.g., 7.0")
        starttime = col_start.text_input("Start Time:", help="e.g., 2025-01-01 10:00:00")
        endtime = col_end.text_input("End Time:")

        st.subheader("Plot Parameters")
        col_sec, col_dp = st.columns(2)
        sec_between_input = col_sec.text_input("Seconds Between Points:")
        dp_count_input = col_dp.text_input("Datapoint Count:")

        # Action Button (Must be inside the form)
        submitted = st.form_submit_button("Fetch & Plot Trend", type="primary")

    # --- Core Logic Execution on Submit ---
    if submitted:
        # Save history immediately after submission
        if idcs_input:
            save_history(idcs_input)
            
        st.status("Processing request...", expanded=True) # Streamlit Status Bar
        
        # Input Validation and Conversion
        try:
            days = float(days_input) if days_input else None
            sec_between = int(sec_between_input) if sec_between_input else None
            dp_count = int(dp_count_input) if dp_count_input else None
        except ValueError:
            st.error("Invalid number entered for Days, Seconds, or Datapoint Count.")
            return

        idcs_list = idcs_input.strip().split() if idcs_input.strip() else None

        # Fetch Data
        try:
            data_buffer, _ = eds_core.fetch_trend_data(
                idcs=idcs_list, 
                starttime=starttime, 
                endtime=endtime, 
                days=days, 
                seconds_between_points=sec_between, 
                datapoint_count=dp_count,
                default_idcs=default_idcs
            )
            
            if data_buffer.is_empty():
                st.warning("Success, but no data points were returned.")
            else:
                st.success("Data successfully fetched. Launching plot...")
                
                # --- Plotting ---
                # This still relies on eds_core.plot_trend_data opening a new tab,
                # which is exactly what you requested.
                eds_core.plot_trend_data(
                    data_buffer, 
                    force_webplot=True, 
                    force_matplotlib=False
                )
                st.info("Plot opened in a new browser tab.")
                
        except BadParameter as e:
            st.error(f"Configuration/Input Error: {str(e).strip()}")
        except Exception as e:
            st.error(f"An unexpected error occurred: {e}")

# --- End Streamlit Function ---

def launch_web():
    """Launches the Streamlit web interface for EDS Trend."""

    st.set_page_config(layout="centered", page_title="EDS Trend")
    st.title("EDS Trend")
    st.markdown("---")
    
    # 1. IDCS Input (Mimics Combo/History - Streamlit handles state automatically)
    with st.container(border=True):
        st.header("Sensor Selection")
        
        # Streamlit doesn't have a direct 'Combo' that saves history like FreeSimpleGUI.
        # For simplicity, we'll use a text input and a checkbox.
        idcs_input = st.text_input(
            "Ovation Sensor IDCS (e.g., M100FI M310LI). Separate with spaces.", 
            key="idcs_list_web"
        )
        default_idcs = st.checkbox(
            "Use Configured Default IDCS", 
            key="default_idcs_web"
        )
        
    st.markdown("---")
    
    # 2. Time Range
    with st.container(border=True):
        st.header("Time Range")
        col1, col2, col3 = st.columns(3)
        
        days_input = col1.text_input("Days:", key="days_web")
        starttime = col2.text_input("Start Time:", key="starttime_web")
        endtime = col3.text_input("End Time:", key="endtime_web")

    st.markdown("---")

    # 3. Plot Options
    with st.container(border=True):
        st.header("Plot Options")
        col_sec, col_dp = st.columns(2)
        
        sec_between_input = col_sec.text_input("Seconds Between Points:", key="seconds_between_points_web")
        dp_count_input = col_dp.text_input("Datapoint Count:", key="datapoint_count_web")

        plot_type = st.radio(
            "Select Plot Environment:",
            ("Web-Based Plot (Plotly)", "Matplotlib Plot (Local)"),
            index=0, # Default to Web-Based
            horizontal=True
        )
        
    st.markdown("---")
    
    # 4. Action Button
    if st.button("Fetch & Plot Trend", key="fetch_button", type="primary"):
        
        # --- Input Validation and Conversion (Similar to GUI) ---
        idcs_list = idcs_input.strip().split() if idcs_input.strip() else None
        
        try:
            days = float(days_input) if days_input else None
            sec_between = int(sec_between_input) if sec_between_input else None
            dp_count = int(dp_count_input) if dp_count_input else None
            
            starttime = starttime if starttime else None
            endtime = endtime if endtime else None
            
            force_webplot = (plot_type == "Web-Based Plot (Plotly)")
            force_matplotlib = (plot_type == "Matplotlib Plot (Local)")

        except ValueError:
            st.error("Invalid number entered for Days, Seconds, or Datapoint Count.")
            return

        # --- Core Logic Execution ---
        try:
            with st.spinner('Fetching data from EDS API...'):
                data_buffer, _ = eds_core.fetch_trend_data(
                    idcs=idcs_list, 
                    starttime=starttime, 
                    endtime=endtime, 
                    days=days, 
                    plant_name=None,
                    seconds_between_points=sec_between, 
                    datapoint_count=dp_count,
                    default_idcs=default_idcs
                )
            
            # --- Status and Plotting ---
            if data_buffer.is_empty():
                st.warning("Success, but no data points were returned for the selected time range and sensors.")
            else:
                st.success("Data successfully fetched. Launching plot...")
                
                # IMPORTANT: Streamlit's plotting needs to be handled *inside* the web app.
                # Your existing plot_trend_data likely launches a separate process/window.
                # For Streamlit, you must pass the data to a Streamlit-compatible plotter.
                
                # Placeholder for the actual Streamlit Plotting logic:
                # Assuming PlotBuffer can easily convert to a Pandas DataFrame:
                # df = data_buffer.to_pandas()
                # st.line_chart(df) 
                
                # If your eds_core.plot_trend_data uses Plotly (the webplot option), 
                # you might need to extract the Plotly figure and pass it to Streamlit:
                
                # fig = eds_core.generate_plotly_figure(data_buffer) # New helper function needed
                # st.plotly_chart(fig, use_container_width=True)
                
                # For now, we'll assume a new plotting function is needed for Streamlit integration:
                st.write("Plotting integration placeholder: The core data is ready.")
                
        except BadParameter as e:
            st.error(f"Configuration/Input Error: {str(e).strip()}")
        except Exception as e:
            st.error(f"An unexpected error occurred during data fetching: {e}")

if __name__ == "__main__":
    is_web_compatible = pyhabitat.web_browser_is_available() and \
                        (pyhabitat.on_termux() or pyhabitat.on_ish_alpine())
    if False:# is_web_compatible:
        #launch_web()
        launch_streamlit()
    
    else:
        launch_fsg(web=True) # Use the desktop version

   
