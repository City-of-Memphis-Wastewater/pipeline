### 🚀 Installation Guide for CLI Users

This guide will walk you through the process of installing and configuring the `pipeline-eds` command-line interface (CLI) for both standard desktop environments and Termux on Android. The CLI requires a Python 3.8+ environment.

#### **Python Setup**

First, ensure you have Python 3.8 or a later version installed on your system.

  * **On Windows**, you can download it from the official Python website. Make sure to check the box to add Python to your PATH during installation.
  * **On macOS**, you can use Homebrew: `brew install python@3.11`.
  * **On Termux (Android)**, use the built-in package manager: `pkg install python`.

-----

### 💻 CLI Installation on Desktop (Windows, macOS, Linux)

**`pipx`** is the recommended tool for installing Python CLIs. It installs applications in isolated environments to prevent conflicts with your other Python projects.

1.  **Install `pipx`**
    If you don't already have it, install `pipx` using `pip`:
    ```bash
    pip install pipx
    ```
2.  **Ensure `pipx` is in your PATH**
    After installing, run `pipx ensurepath` to make sure the commands are accessible from your terminal. You may need to restart your terminal session for the changes to take effect.
    ```bash
    pipx ensurepath
    ```
3.  **Install `pipeline-eds`**
    Install the package from PyPI. If you are on Windows, you can optionally include the `[windows]` extras to get the dependencies for `matplotlib` and `pyodbc`.
    ```bash
    pipx install pipeline-eds
    # For Windows users:
    pipx install "pipeline-eds[windows]"
    ```
4.  **First-time Configuration**
    The first time you run a command that requires credentials, like `eds trend`, the CLI will prompt you to configure them.
    ```bash
    eds trend M100FI FI8001 --start "Sept 19"
    ```
    Upon running this command for the first time, you will be prompted to enter and securely save your EDS API credentials (URL, username, and password). This is a one-time process. The next time you run a command, it will use the saved credentials.

-----

### 📱 CLI Installation on Termux (Android)

For Termux, the process is similar but without the use of `pipx` due to environment limitations.

1.  **Install Python**
    Ensure Python is installed:
    ```bash
    pkg install python
    ```
2.  **Install Dependencies**
    Clone the repository to get the `requirements.txt` file, then install the dependencies directly with `pip`.
    ```bash
    git clone https://github.com/City-of-Memphis-Wastewater/pipeline.git
    cd pipeline
    pip install -r requirements.txt
    ```
3.  **First-time Configuration**
    Just like the desktop version, the CLI will prompt you to configure credentials on the first run.
    ```bash
    python -m pipeline trend M100FI FI8001 --start "one day ago"
    ```

The video provides a tutorial on installing Python and related tools in the Termux environment on an Android device.

[https://www.youtube.com/watch?v=HarwU8bxvTQ](https://www.youtube.com/watch?v=HarwU8bxvTQ)
