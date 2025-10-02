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



def get_self_closing_html(message: str, delay_seconds: float = 1.0) -> str:
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