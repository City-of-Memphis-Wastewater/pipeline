# pipeline/interfaces/gui_eds.py

import FreeSimpleGUI as sg
from typer import BadParameter
from pipeline.core import eds as eds_core

def launch_fsg_():
    layout = [[sg.Text("EDS Trend")],
          [sg.Text("Which Ovation sensors do you want to see? Input IDCS values. Example: M100FI M310LI FI8001. Leave empty for the default.")],
          [sg.InputText(key = "idcs_list")],
          [sg.Text("Designate a start time, an end time, and/or a number of days.")],
          [sg.Text("Days: "),sg.InputText(key = "days"), sg.Text("Start: "), sg.InputText(key = "starttime"), sg.Text("End: "), sg.InputText(key = "endtime")],
          [sg.OK(), sg.Cancel()]]

    window = sg.Window("EDS Trend", layout)

    event, values = window.read()
    window.close()

    #your_color = values["days"]
    sg.popup(f"Values: {values}")


# Set theme for a slightly better look
sg.theme('SystemDefault') 

def launch_fsg():
    """Launches the FreeSimpleGUI interface for EDS Trend."""
    
    # Define the layout
    layout = [
        [sg.Text("EDS Trend", font=("Helvetica", 16))],
        [sg.HorizontalSeparator()],
        
        [sg.Text("Ovation Sensor IDCS (e.g., M100FI M310LI). Separate with spaces. Leave empty to use configured defaults.", size=(70, 2))],
        [sg.InputText(key="idcs_list", size=(70, 1))],
        [sg.Checkbox("Use Configured Default IDCS", key="default_idcs", default=False)],
        
        [sg.HorizontalSeparator()],
        
        [sg.Text("Time Range (Start/End/Days)", font=("Helvetica", 12))],
        [sg.Text("Days:", size=(10, 1)), sg.InputText(key="days", size=(15, 1)), 
         sg.Text("Start Time:", size=(10, 1)), sg.InputText(key="starttime", size=(25, 1)), 
         sg.Text("End Time:", size=(10, 1)), sg.InputText(key="endtime", size=(25, 1))],
        
        [sg.HorizontalSeparator()],

        [sg.Text("Plot Options", font=("Helvetica", 12))],
        [sg.Text("Time Step/Datapoints (Leave empty for automatic):", size=(40, 1))],
        [sg.Text("Seconds Between Points:", size=(20, 1)), sg.InputText(key="seconds_between_points", size=(10, 1)),
         sg.Text("Datapoint Count:", size=(15, 1)), sg.InputText(key="datapoint_count", size=(10, 1))],
        
        [sg.Checkbox("Force Web-Based Plot (Plotly)", key="force_webplot", default=True, tooltip="Uses Plotly/browser. Recommended for most users."),
         sg.Checkbox("Force Matplotlib Plot (Local)", key="force_matplotlib", default=False, tooltip="Uses Matplotlib. Requires a local display environment.")],
        
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
                    sg.popup_ok("Success, but no data points were returned for the selected time range and sensors.")
                else:
                    # --- Plotting ---
                    sg.popup_ok("Data successfully fetched. Launching plot...")
                    eds_core.plot_trend_data(data_buffer, force_webplot, force_matplotlib)
                    
            except BadParameter as e:
                # Catch the specific error raised by the core logic
                sg.popup_error("Configuration/Input Error:", str(e).strip())
            except Exception as e:
                # Catch all other unexpected errors
                sg.popup_error("An unexpected error occurred during data fetching:", str(e))

    window.close()

if __name__ == "__main__":
    launch_fsg()

if __name__ == "__main__":
    launch_fsg()
