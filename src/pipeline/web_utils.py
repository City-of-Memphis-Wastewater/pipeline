# pipeline/webtools.py
import webbrowser
import shutil
import subprocess
import time

# --- Browser Launch Logic ---

def launch_browser(url: str):
    """
    Attempts to launch the URL using specific platform commands first, 
    then falls back to the standard Python webbrowser, ensuring a new tab is opened.
    Includes a delay for stability.
    """
    
    launched = False
    
    # 1. Try Termux-specific launcher
    if shutil.which("termux-open-url"):
        try:
            print("[WEBPROMPT] Attempting launch using 'termux-open-url'...")
            # Run the command without capturing output to keep it clean
            subprocess.run(["termux-open-url", url], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            launched = True
            return
        except subprocess.CalledProcessError as e:
            print(f"[WEBPROMPT WARNING] 'termux-open-url' failed: {e}. Falling back...")
        except FileNotFoundError:
             pass

    # 2. Try general Linux desktop launcher
    if shutil.which("xdg-open"):
        try:
            print("[WEBPROMPT] Attempting launch using 'xdg-open'...")
            subprocess.run(["xdg-open", url], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            launched = True
            return
        except subprocess.CalledProcessError as e:
            print(f"[WEBPROMPT WARNING] 'xdg-open' failed: {e}. Falling back...")
        except FileNotFoundError:
             pass
             
    # 3. Fallback to standard Python library
    try:
        print("[WEBPROMPT] Attempting launch using standard Python 'webbrowser' module...")
        webbrowser.open_new_tab(url)
        launched = True
    except Exception as e:
        print(f"[WEBPROMPT ERROR] Standard 'webbrowser' failed: {e}. Please manually open the URL.")

    # Add a brief delay after a successful launch for OS stability
    if launched:
        time.sleep(0.5)



def get_self_closing_html_defunct(message: str, delay_seconds: float = 1.0) -> str:
    """
    Generates a simple HTML page that displays a message and automatically 
    closes the browser window/tab after a specified delay.
    
    This is ideal for use as a final response in web-based prompts (like
    the CherryPy configuration screen) to ensure the browser tab closes 
    cleanly after the user submits data, allowing the main script to proceed.

    Args:
        message (str): The primary message to display to the user.
        delay_seconds (float): The time (in seconds) before the window attempts to close.
    
    Returns:
        str: The complete HTML content.
    """
    delay_ms = int(delay_seconds * 1000)
    
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Input Received</title>
    <style>
        body {{
            font-family: Inter, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
            background-color: #f4f4f9;
            color: #333;
            text-align: center;
        }}
        .container {{
            padding: 40px;
            background: white;
            border-radius: 12px;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
        }}
        h1 {{
            color: #3b82f6;
            margin-bottom: 20px;
        }}
        p {{
            font-size: 1.1em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Success!</h1>
        <p>{message}</p>
        <p>This window will close in {delay_seconds:.1f} seconds...</p>
    </div>
    
    <script>
        // Use setTimeout to introduce a slight delay ({delay_ms}ms)
        setTimeout(function() {{
            console.log("Attempting to close window after submission.");
            // window.close() only works if the window was opened by script,
            // but it's the standard way to try to close the tab.
            window.close(); 
        }}, {delay_ms});
    </script>
</body>
</html>
"""
    return html_content


def get_self_closing_html_safe(message: str, delay_seconds: float = 1.0) -> str:
    """
    Generates an HTML page that displays a success message and uses JavaScript 
    to automatically close the browser tab after a specified delay. It also
    provides a manual 'Close' button as a fallback if automatic closure fails.
    
    This function is used by the server's submission endpoint to signal completion.
    """
    # Convert delay to milliseconds for JavaScript's setTimeout
    delay_ms = int(delay_seconds * 1000)
    
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Submission Complete</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script>
        // Use a timeout to ensure the user sees the message before the tab closes
        setTimeout(function() {{
            // This is the critical line that attempts to close the window/tab.
            // Note: Modern browsers may restrict this if the window was not 
            // opened via script, but it is the standard mechanism.
            window.close();
        }}, {delay_ms});
    </script>
    <style>
        /* Updated to dark theme */
        body {{ 
            background-color: #1f2937; /* Dark background */
            color: #f3f4f6; /* Light text */
            font-family: 'Inter', sans-serif; 
            display: flex; 
            justify-content: center; 
            align-items: center; 
            height: 100vh; 
            margin: 0; 
            padding: 20px;
        }}
        .message-box {{ 
            background-color: #374151; /* Slightly lighter dark background for the box */
            color: #f3f4f6; 
            padding: 40px; 
            border-radius: 12px; 
            text-align: center; 
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.5); 
            min-width: 300px;
            max-width: 90%;
            border: 1px solid #4b5563;
        }}
        h2 {{ 
            margin-top: 0; 
            font-size: 1.8em;
            color: #10b981; /* Success color for heading */
        }}
        p {{ 
            font-size: 1.1em;
            margin-bottom: 20px;
        }}
        .close-button {{
            background-color: #10b981; /* Emerald green button */
            color: #1f2937;
            border: none;
            padding: 10px 20px;
            border-radius: 8px;
            font-size: 1em;
            cursor: pointer;
            transition: background-color 0.2s;
            font-weight: bold;
        }}
        .close-button:hover {{
            background-color: #059669;
        }}
    </style>
</head>
<body>
    <div class="message-box">
        <h2>Success!</h2>
        <p>{message}</p>
        <p>This window will attempt to close automatically in {delay_seconds} seconds.</p>
        <button class="close-button" onclick="window.close()">Close Tab Now</button>
    </div>
</body>
</html>
"""
    return html_content


def get_self_closing_html(message: str, delay_seconds: float = 1.0) -> str:
    """
    Generates an HTML page that displays a success message and uses JavaScript 
    to automatically close the browser tab after a specified delay. It also
    provides a manual 'Close' button as a fallback if automatic closure fails.
    
    This function is used by the server's submission endpoint to signal completion.
    """
    # Convert delay to milliseconds for JavaScript's setTimeout
    delay_ms = int(delay_seconds * 1000)
    
    
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Submission Complete</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script>
        // The automatic close attempt:
        setTimeout(function() {{
            // This line fails due to browser security restrictions on externally launched tabs.
            window.close();
        }}, {delay_ms});
    </script>
    <style>
        /* Updated to dark theme */
        body {{ 
            background-color: #1f2937; /* Dark background */
            color: #f3f4f6; /* Light text */
            font-family: 'Inter', sans-serif; 
            display: flex; 
            justify-content: center; 
            align-items: center; 
            height: 100vh; 
            margin: 0; 
            padding: 20px;
        }}
        .message-box {{ 
            background-color: #374151; /* Slightly lighter dark background for the box */
            color: #f3f4f6; 
            padding: 40px; 
            border-radius: 12px; 
            text-align: center; 
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.5); 
            min-width: 300px;
            max-width: 90%;
            border: 1px solid #4b5563;
        }}
        h2 {{ 
            margin-top: 0; 
            font-size: 1.8em;
            color: #10b981; /* Success color for heading */
        }}
        p {{ 
            font-size: 1.1em;
            margin-bottom: 20px;
        }}
        .close-button {{
            background-color: #10b981; /* Emerald green button */
            color: #1f2937;
            border: none;
            padding: 10px 20px;
            border-radius: 8px;
            font-size: 1em;
            cursor: pointer;
            transition: background-color 0.2s;
            font-weight: bold;
            margin-top: 15px; /* Added spacing */
        }}
        .close-button:hover {{
            background-color: #059669;
        }}
        .fallback-instruction {{
            margin-top: 25px;
            font-size: 0.9em;
            color: #9ca3af; /* Gray text for instruction */
        }}
    </style>
</head>
<body>
    <div class="message-box">
        <h2>Configuration Saved!</h2>
        <p>{message}</p>
        <p>The application has successfully received your input and continued execution.</p>
        
        <!-- Updated the button to try window.close() AND redirect to a blank page -->
        <button class="close-button" onclick="window.close(); window.location.replace('about:blank');">Close or Clear Tab</button>
        
        <p class="fallback-instruction">
            (If the tab doesn't close, clicking the button will at least clear the content to a blank page. 
            You can then safely close the tab manually.)
        </p>
    </div>
</body>
</html>
"""
    return html_content