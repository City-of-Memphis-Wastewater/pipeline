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
    After installing, run `pipx ensurepath` or `python -m pipx ensurepath` to make sure the commands are accessible from your terminal. You may need to restart your terminal session for the changes to take effect.
    ```bash
	python -m pipx ensurepath
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
    eds trend M100FI FI8001 --start "Sept 18"
    ```
    Upon running this command for the first time, you will be prompted to enter and securely save your EDS API credentials (URL, username, and password). This is a one-time process. The next time you run a command, it will use the saved credentials.

-----

### 📱 CLI Installation on Termux (Android)

For Termux, the process is similar but without the use of `pipx` due to environment limitations.

1.  **Install Python**
    Ensure Python is installed:
    ```bash
	pkg update && pkg upgrade
    pkg install python
    ```
2.  **Install pipx**
    Prepare to install Python-based CLI tool(s).
    ```bash
    pip install pipx
	python -m pipx ensurepath
	source ~/.bashrc # Or simply exit the Termux app and restart it.
	pipx --version
    ```
3.  **Install `pipeline-eds`**
    Install the package from PyPI.
    ```bash
    pipx install pipeline-eds
	```
4.  **First-time Configuration**
    Just like the desktop version, the CLI will prompt you to configure credentials on the first run. You do not need quotes in your `--start` or `--end` values if the strings do not have spaces (commas are okay either way).
    ```bash
    eds trend M100FI FI8001 --start Sept18
    ```

---

### 🛠 ️ Correcting Configuration Mistakes

If you made a mistake when entering a configuration value or credential, you have two primary ways to correct it using the `configure` command.

<br>
<hr>
<br>

#### **1. Using the `--overwrite` Flag**

The **`--overwrite`** (or shorthand **`-o`**) flag forces the `configure` command to re-prompt you for every credential, even if it's already set. This is the recommended way to correct a single mistake or update a credential.

Running the command with this flag will show you your existing configuration and ask for confirmation before overwriting it.

```bash
pipeline configure --overwrite
```

  * The CLI will start the guided setup again.
  * For each existing value, it will show the current setting and ask, "Do you want to overwrite it?"
  * Select **yes** for the values you want to change and **no** for the ones you want to keep.

<br>
<hr>
<br>

#### **2. Using the `--textedit` Flag**

For more advanced users or for making multiple changes at once, the **`--textedit`** (or shorthand **`-t`**) flag opens the configuration file directly in your default text editor.

```bash
pipeline configure --textedit
```

This option is useful for:

  * Directly editing non-secret values like URLs or file paths.
  * Making bulk changes to the configuration without going through the guided prompt.

**Note:** The `--textedit` flag only opens the non-secret configuration file (`config.json`). **It does not grant access to the securely stored credentials in your system's keyring.** To update secrets like passwords, you must use the **`--overwrite`** flag.

The video provides a tutorial on installing Python and related tools in the Termux environment on an Android device.

[https://www.youtube.com/watch?v=HarwU8bxvTQ](https://www.youtube.com/watch?v=HarwU8bxvTQ)

