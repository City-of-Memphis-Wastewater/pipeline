# `pipeline-eds`

`pipeline-eds` is a Python project designed to simplify API access to Emerson Enterprise Data Server (EDS) machines. It facilitates seamless data exchange between Emerson's Ovation local systems and various external parties, including third-party contractors and internal employees. The project is distributed on PyPI under the package name `pipeline-eds`.

<br>
<hr>
<br>

## 🚀 Getting Started

This section provides a quick guide to help you get `pipeline` up and running. Choose the setup method that best suits your needs: CLI-only usage or local development.

### 💻 CLI Installation (Recommended for End-Users)

For a simple command-line interface (CLI) experience, **`pipx`** is the recommended installation method. `pipx` installs and runs Python applications in isolated environments, preventing conflicts with your system's Python packages.

1.  **Install `pipx`**
    If you don't have `pipx` installed, you can get it with `pip`:
    ```bash
    pip install pipx
    pipx ensurepath
    ```
2.  **Install `pipeline-eds` with `pipx`**
    Install the package directly from PyPI. If you need Windows-specific dependencies like `pyodbc` and `matplotlib`, use the `[windows]` extra.
    ```bash
    pipx install pipeline-eds
    # For Windows users:
    pipx install "pipeline-eds[windows]"
    ```
3.  **Run CLI Commands**
    The `pyproject.toml` file defines `pipeline`, `eds`, and `pipeline-eds` as command-line aliases. Once installed, you can use any of these aliases directly from your terminal.
    ```bash
    eds configure
    eds trend M100FI --start June3 --end June17
    ```

### 🛠️ Developer & Contributor Setup

If you plan to contribute to the project or need to work with the source code, follow these steps to set up a full development environment.

1.  **Clone the Repository**
    Start by cloning the project from GitHub and navigating into the directory:
    ```bash
    git clone https://github.com/City-of-Memphis-Wastewater/pipeline.git
    cd pipeline
    ```
2.  **Install `pyenv` and `Poetry`**
    This project uses **`pyenv`** for managing Python versions and **`Poetry`** for dependency management. This combination ensures a clean, reproducible development environment without interfering with your system's Python installation.
      * **Install `pyenv`:** Refer to the official `pyenv` documentation for your operating system ([pyenv-win](https://github.com/pyenv-win/pyenv-win) for Windows, [pyenv](https://github.com/pyenv/pyenv) for Linux/macOS).
      * **Install `Poetry`:** See the [Poetry documentation](https://www.google.com/search?q=https://python-poetry.org/docs/%23installation) for installation instructions.
3.  **Configure the Environment**
    Use `pyenv` to set the Python version for the project and then tell Poetry to use that version:
    ```bash
    pyenv install 3.11.9
    pyenv local 3.11.9
    poetry env use 3.11.9
    ```
4.  **Install Dependencies**
    Poetry will read the `pyproject.toml` file and install all necessary packages into a new virtual environment:
    ```bash
    poetry install
    ```
5.  **Run Development Commands**
    Once installed, you can execute commands using `poetry run`:
    ```bash
    poetry run python -m pipeline.env
    poetry run eds ping
    ```
    This ensures that all commands run within the project's isolated environment.

<br>
<hr>
<br>

## ✨ Tips for Optimal Usage & Maintenance
To ensure a smooth and efficient experience with `pipeline-eds`, consider the following best practices:

### Keep `pipeline-eds` Updated: 
Regularly upgrade your `pipeline-eds` installation to benefit from the latest features, bug fixes, and performance improvements.
```bash
pipx upgrade pipeline-eds
```
This command will update pipeline-eds and its dependencies in its isolated pipx environment.

### Maintain Your Python Environment:

- Desktop Users: While `pipx` isolates `pipeline-eds`, it's good practice to keep your underlying Python installation updated.
- Termux Users: Regularly update your Termux environment and packages to ensure compatibility and security:
```bash
pkg update && pkg upgrade
```

### Understanding eds configure and Credential Management:
The first time you execute a command requiring access to your EDS API (e.g., eds trend), `pipeline-eds` will guide you through a one-time configuration process. Your sensitive API credentials (URL, username, password) are securely stored using your operating system's native keyring service. This is a robust and secure method that avoids storing plaintext passwords in files. If your credentials change, you can re-run eds configure at any time to update them.

### Network Connectivity (VPN Essential):
A critical requirement for `pipeline-eds` to function is proper network connectivity to your Emerson Ovation EDS machine. If your EDS server is located on a private network (e.g., within your organization's internal network), you must be connected to the appropriate Virtual Private Network (VPN). Failure to do so will result in connection errors when `pipeline-eds` attempts to fetch data.

### Leveraging Flexible Date/Time Inputs:
The `eds trend` command offers highly flexible date and time parsing for its --start and --end options, thanks to the `pendulum` package. You can use a wide variety of natural language inputs, such as:

- `--start "2023-09-18"`
- `--start "Sept 18"`
- `--start "a week ago"`
- `--start "yesterday 9am"`
- `--end "now"` 
Experiment with different formats to suit your query needs. Remember to use quotes around values if they contain spaces.

<br>
<hr>
<br>

## 🔐 Security & Configuration

`pipeline` uses a two-tiered approach to manage configuration and secrets.

  * **Non-Sensitive Configuration**: Non-sensitive settings like URLs and paths are stored in a local JSON file (`~/.pipeline-eds/config.json`). This file is easy to inspect and manage.
  * **Secrets and Credentials**: For CLI users, API credentials and passwords are **securely stored** using your operating system's native keyring. This is a much safer alternative to storing plaintext passwords in a file. The `pipeline configure` command guides you through this one-time setup process.

**Note for Developers**: While the CLI now uses the keyring, some functionality within the codebase still relies on the `secrets.yaml` file for credential management. This file is not required for general CLI usage but may be necessary for specific development workflows and legacy components.

**Important**: You must be on the same network as your server (e.g., via a VPN) if it is not publicly accessible.

<br>
<hr>
<br>

## ⚙️ Project Implementation & Use Cases

`pipeline` is designed to be deployed as a scheduled task on a Windows server.

  * The project is executed by **Windows Task Scheduler**, which calls a PowerShell script (`main_eds_to_rjn_quiet.ps1`) as the entry point.
  * The iterative timing (e.g., hourly execution) is handled by the `Task Scheduler`, not by Python.
  * For these automated tasks, a standard `venv` is used, as `Task Scheduler` can run under different user accounts.

<br>
<hr>
<br>

## 📱 Running on Android (`Termux`)

The `pipeline` project can be installed and run on Android devices using the **Termux** terminal emulator. **CLI installation via `pipx` is the recommended method for Termux users, as development is not expected in this environment.**

### Termux Limitations

  * **No `pyenv` or `Poetry`**: Package management must be done with `pip` directly. You can and should use `venv`.
  * **Limited Library Support**: Some libraries that require compilation (e.g., `pandas`, `numpy`) or have GUI dependencies are not supported on Termux.
  * **HTML Viewer**: You may need to manually configure the default `HTML` viewer to a full-featured browser on Android.

### 🌐 Termux and Web-Based Visuals (Plotly)
When using pipeline-eds in Termux to generate plots (e.g., with eds trend), the visuals are displayed as web-based HTML pages using libraries like Plotly. Instead of directly opening a graphical window (which is not typically supported by Termux's command-line environment), `pipeline-eds serves` these HTML files via a local web server (often on localhost).

### Why localhost and Manual Opening?

- Termux Sandboxing: Termux operates in a sandboxed environment on Android. This security measure restricts direct access to certain system resources, including the ability to automatically launch web browsers or other GUI applications from the command line.
- Local Server Approach: To work around this, pipeline-eds acts as a small web server, making the generated HTML plot accessible at a specific localhost URL (e.g., [http://127.0.0.1:8000.](http://127.0.0.1:8000`.)
- Manual Opening: Due to the sandboxing, Termux cannot automatically open this URL in your default Android browser. You must manually copy the provided URL from the Termux output and paste it into your preferred web browser (e.g., Chrome, Firefox) on your Android device. This allows your full-featured browser to render the interactive Plotly graph.
- Security: This approach is also a security measure, ensuring that applications within Termux explicitly serve content, and the user consciously decides to open it in a less restricted environment (the browser).  
  
<br>
<hr>
<br>

## 📝 Final Note on Naming
The project is internally referred to as pipeline, but the PyPI package is named pipeline-eds to avoid a name conflict with an existing, unrelated package on PyPI. For CLI usage, the pyproject.toml file creates aliases so you can use pipeline, eds, and pipeline-eds interchangeably in your terminal. This allows for a more intuitive command-line experience without the need to use the full PyPI package name.