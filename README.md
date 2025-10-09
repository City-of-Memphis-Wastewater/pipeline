# `pipeline-eds`

`pipeline-eds` is a Python project designed to simplify API access to Emerson Enterprise Data Server (EDS) machines. It facilitates seamless data exchange between Emerson's Ovation local systems and various external parties, including third-party contractors and internal employees. The project is distributed on PyPI under the package name `pipeline-eds`.

<br>
<hr>
<br>

## 🚀 Getting Started

This section provides a quick guide to help you get `pipeline` up and running. Choose the setup method that best suits your needs: CLI-only usage or local development.

### 💻 CLI Installation (Recommended for End-Users)

For a simple command-line interface (CLI) experience, **`pipx`** is the recommended installation method. `pipx` installs and runs Python applications in isolated environments, preventing conflicts with your system's Python packages.
For more information about installing Python, pip, and any environment-specific dependencies, see the section below, `Building from Source (pip)`.

1.  **Install `pipx`**
    If you don't have `pipx` installed, you can get it with `pip`:
    ```bash
    pip install pipx
    python -m pipx ensurepath
    ```
2.  **Install `pipeline-eds` with `pipx`**
    Install the package directly from PyPI. If you need Windows-specific dependencies like `pyodbc` and `matplotlib`, use the `[windows]` extra.
    ```bash
    pipx install pipeline-eds
    # For Windows users. who want to use matplotlib:
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
    poetry run python -m pipeline.cli
    poetry run eds ping # 
    ```
    This ensures that all commands run within the project's isolated environment.
	You can run `poetry run eds` directly because of the `[tool.poetry.scripts]` section in the `pyproject.toml`, which states that `eds = "pipeline.cli:app"`.
	
### 🛠️ Alternative Setup: Building from Source (pip)
This method is necessary for environments like Termux and Alpine/iSH where full Poetry support is not practical or where you prefer to use standard pip for dependency management after cloning the repository or unpacking the .tar.gz source distribution.

##### For Termux (Android)
Termux does not support Poetry. You must manually install system dependencies and then use pip in a virtual environment.

1.  Install Python and System Dependencies

```bash     
# Update package lists and upgrade existing packages
pkg update && pkg upgrade -y
# Install core Termux packages needed for Python scientific libraries
pkg install python python-pip python-numpy rust clang make
```

2.  Create and Activate a Virtual Environment
    *Though not strictly required by Termux, using a virtual environment is a strong best practice.*
    
```bash
python -m venv .venv     
source .venv/bin/activate
```
   
3.  Install Python Dependencies
    First, generate the requirements.txt file from pyproject.toml (if not already present), then install.    
```bash
pip install -r requirements.txt 
```
4.  Run Commands

```bash
python -m pipeline.cli configure     
```
##### For Alpine Linux / iSH (iOS)
Alpine uses MUSL, which requires installing specific package variants. `cryptography`, `keyring`, and `numpy` are notable blockers due to MUSL compatibility, but a workaround is possible.

1.  Install System Dependencies
    
```bash     
# Install pip and the required cryptography backend for MUSL
apk update
apk add python3 \
    py3-pip \
    gcc \
	musl-dev \
	build-base \
	py3-cryptography \
	py3-numpy
```
     
2.  Create and Activate a Virtual Environment
    *Using a virtual environment is a strong best practice for keeping your system Python clean and consolidating .*
   
```bash 
python3 -m venv .venv
source .venv/bin/activate
```

3.  Install Python Dependencies
```bash 
pip install -r requirements.txt
```
4.  Run Commands

```bash 
python3 -m pipeline.cli trend M100FI
```

<br>
<hr>
<br>

## 📦 Distribution and Packaging

This project supports multiple packaging formats to make installation flexible across platforms.  
While some formats allow installation on systems without internet access, note that the **application itself requires internet connectivity** to call its API.

### 🔹 Executables (`.exe`, `.elf`)
- **Generated by**: [`build_executable.py`](./build_executable.py)
- **Variants**:
  - **Windows `.exe`**: Tested on Windows 11. Runs standalone without requiring Python.
  - **Linux `.elf`**:
    - Built on **WSL2 Ubuntu** for general Linux systems.
    - Built on **Termux** for Android devices.  
      - Smoothest rollout on Termux: no need to install Python separately.
      - Avoids the `.shortcuts` widget permission error seen with `.pyz`.
- **Internet required for install**: ❌ (binaries can be copied directly)  
- **Internet required for use**: ✅ (API calls)  

### 🔹 Python Zip App (`.pyz` + `.bat`)
- **Generated by**: [`build_shiv.sh`](./build_shiv.sh) on WSL2 Ubuntu
- **Best for**: Systems that already have Python installed.
- **Windows support**: A `.bat` launcher is provided for smoother execution.
- **Termux notes**:
  - Works, but calling `.pyz` from the Termux `.shortcuts` widget can trigger a **permission error**.
  - Requires Python to be installed on Termux.
- **Maintainability**: Easier to update regularly compared to static binaries.
- **Internet required for install**: ❌ (once `.pyz` is copied)  
- **Internet required for use**: ✅  

### 🔹 `pipx` Install
- **Best for**: Staying current with rolling changes.
- **Update shortcut**: On Termux, an update shortcut is available directly from the home screen widget.
- **Requirements**: Python and `pipx` installed.
- **Internet required for install/update**: ✅  
- **Internet required for use**: ✅  

### 🔹 Source Distributions (`.tar.gz`, `.whl`)
- **Generated by**: Poetry
- **Best for**: Developers or environments where building from source is preferred.
- **Internet required for install**: ✅ (to fetch dependencies)  
- **Internet required for use**: ✅  

### 🔹 Docker Containers
- **Generated by**: Dockerfiles in the repository
- **Best for**: Containerized deployments where dependencies and environment isolation are important.
- **Notes**:
  - Provides a reproducible runtime environment.
  - Useful for CI/CD pipelines or server deployments.
  - Currently built manually; orchestration (e.g., automated builds, registry publishing) is a **future goal**.
- **Internet required for install**: ✅ (to pull base images and dependencies)  
- **Internet required for use**: ✅  

### 🌐 Connectivity Summary

| Format          | Install Without Internet | Python Needed | Best Use Case |
|-----------------|--------------------------|---------------|---------------|
| `.exe`          | Yes                      | No            | Windows systems, simple rollout |
| `.elf` (Ubuntu) | Yes                      | No            | Linux servers/desktops |
| `.elf` (Termux) | Yes                      | No            | Android/Termux, smoothest rollout |
| `.pyz` + `.bat` | Yes                      | Yes           | Python‑ready systems, maintainable updates |
| `pipx`          | No                       | Yes           | Always‑updated installs, Termux widget support |
| `.tar.gz`/`.whl`| No                       | Yes           | Developers building from source |
| Docker          | No (manual build)        | No            | Containerized deployments, CI/CD |

---

### ⚠️ Notes and Limitations
- These packages simplify **installation** on disconnected systems, but the application itself requires internet access to function (API calls).
- **Alpine / iSH (iPhone)**: MUSL‑compatible packaging is not yet available. The main barrier is credential storage, as current builds rely on `cryptography` and `keyring`.
- **Docker orchestration**: Currently builds are processed manually. Future goals include automated orchestration and registry publishing.

---

## 🛠️ Build Scripts

### `build_executable.py`
- Automates creation of `.exe` and `.elf` binaries.
- Targets:
  - Windows standalone `.exe`
  - Linux `.elf` (both WSL2 Ubuntu and Termux builds)
- Intended for distributing binaries to systems without requiring Python ins>
- Currently run manually; future goal is to integrate into an automated buil>

### `build_shiv.sh`
- Automates creation of `.pyz` zipapps and corresponding `.bat` launchers.
- Targets:
  - Cross‑platform `.pyz` archives
  - Windows `.bat` wrapper for smooth launching
- Provides a maintainable, portable distribution option for Python‑ready sys>
- Currently run manually; orchestration and CI/CD integration are planned.

---

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
pkg install rust
```

### Understanding eds configure and Credential Management:
The first time you execute a command requiring access to your EDS API (e.g., eds trend), `pipeline-eds` will guide you through a one-time configuration process. Your sensitive API credentials (URL, username, password) are securely stored using your operating system's native keyring service. This is a robust and secure method that avoids storing plaintext passwords in files. If your credentials change, you can re-run eds configure at any time to update them.

### Network Connectivity (VPN Essential):
A critical requirement for `pipeline-eds` to function is proper network connectivity to your Emerson Ovation EDS machine. If your EDS server is located on a private network (e.g., within your organization's internal network), you must be connected to the appropriate Virtual Private Network (VPN). Failure to do so will result in connection errors when `pipeline-eds` attempts to fetch data.

### Leveraging Flexible Date/Time Inputs:
The `eds trend` command offers highly flexible date and time parsing for its --start and --end options, thanks to the `pendulum` package. You can use a wide variety of natural language inputs, such as:

- `--start "2023-09-18"`
- `--start "Sept 18"`
- `--end "now"` 

Experiment with different formats to suit your query needs. Remember to use quotes around values if they contain spaces.
It would be great if terms like "yesterday" worked, but these fail to be recognized by `pendulum`.

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

The `pipeline` project can be installed and run on Android devices using the **[Termux](https://termux.dev/)** terminal emulator.  
For most users, **CLI installation via `pipx` is the recommended method**, as development is not expected in this environment and `pipx` provides the smoothest way to stay up to date.

### Termux Installation Options

There are several ways to run `pipeline` inside Termux, depending on your needs:

- **`pipx` (Recommended)**  
  - Provides rolling updates and integrates with the Termux home‑screen widget.  
  - As of **v0.3.8**, you can add a **shortcut button** to update `pipeline` directly from the Termux widget without opening the terminal.  
  - Requires Python and `pipx` to be installed.  
  - Best choice if you want to keep up with frequent changes.

- **Native ELF Binary**  
  - A prebuilt `.elf` binary is available specifically for Termux.  
  - Runs without requiring Python to be installed.  
  - Avoids the `.shortcuts` widget permission error that can occur when launching `.pyz` apps.  
  - Smoothest rollout for users who just want the CLI tool without managing Python environments.

- **`.pyz` Zipapp**  
  - Works if Python is already installed in Termux.  
  - More maintainable than static binaries since you can replace the `.pyz` file with newer versions.  
  - ⚠️ Known limitation: launching `.pyz` directly from the Termux `.shortcuts` widget may trigger a **permission error**.

---

### Termux Limitations

- **No `pyenv` or `Poetry`**: Package management must be done with `pip` directly. You can and should use `venv` for isolation.  
- **Limited Library Support**: Some libraries that require native compilation (e.g., `pandas`, `numpy`) or GUI dependencies are not supported on Termux.  
- **HTML Viewer**: You may need to manually configure the default HTML viewer to a full‑featured browser on Android.  

### Comparable Apple iPhone Rollout

- **Alpine (iSH on iOS)**: Not yet supported; credential storage via `cryptography` and `keyring` is the current blocker because they are not MUSL compatible..

---

### ✅ Recommendations

- Use **`pipx`** if you want the latest updates and widget integration.  
- Use the **native ELF binary** if you want the simplest, no‑Python setup.  
- Use **`.pyz`** only if you already have Python installed and are comfortable updating the archive manually.



### 🌐 Termux and Web-Based Visuals (Plotly)
When using `pipeline-eds` in Termux to generate plots (e.g., with `eds trend`), the visuals are displayed as web-based HTML pages using libraries like Plotly. Instead of directly opening a graphical window (which is not typically supported by Termux's command-line environment), `pipeline-eds serves` these HTML files via a local web server (often on localhost).

### Why localhost

- Termux Sandboxing: Termux operates in a sandboxed environment on Android. This security measure restricts direct access to certain system resources, including the ability to automatically launch web browsers or other GUI applications from the command line.
- Local Server Approach: To work around this, `pipeline-eds` acts as a small web server, making the generated HTML plot accessible at a specific localhost URL (e.g., [http://127.0.0.1:8000.](http://127.0.0.1:8000`.)
- Manual Opening: Improvemenrs have been made using `xdg-open` and `termux-url-open`, so manual opening of web graphics is no longer required. Due to the sandboxing, Termux has limited ways to automatically open this URL in your default Android browser, but it is possible and now suceeds. Another approach is the `am` command, or `termux-api` but those are not used in this package. If for any reason auyomatic launching fails, you canmanually copy the provided URL from the Termux output and paste it into your preferred web browser (e.g., Chrome, Firefox) on your Android device. This allows your full-featured browser to render the interactive Plotly graph.
- Security: Localhost-based plotting is also a security measure, ensuring that applications within Termux explicitly serve content, and the user is able to view it in a secure yet less restricted environment (the browser).  Using localhost allows for a minimal Termux installation, like from the Pay Store, without relying on `termux-gui` or `x11`.
  
<br>
<hr>
<br>

## 🐍 Python Version Compatibility

The `pipeline-eds` project is designed to support a broad range of modern Python versions, from Python 3.8 up to the latest stable releases, ensuring accessibility across various operating environments (desktop, server, and mobile environments like Termux).

### Supported Python Versions

The project officially supports the following CPython versions:

| Python Version                | Status              | Key Dependency Notes                                                                                                                                                                                                                                                                           |
| ----------------------------- | ------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **3.11 / 3.12 / 3.13 / 3.14** | ✅ Fully Supported   | Runs on the latest major versions of all dependencies (e.g., `keyring` v25+, `pendulum` v3+, `urllib3` v2+).                                                                                                                                                                                   |
| **3.10**                      | ✅ Fully Supported   | Stable; uses latest dependencies, with specific `numpy` and `matplotlib` pins.                                                                                                                                                                                                                 |
| **3.9**                       | ✅ Fully Supported   | Stable; this version marks the transition to modern dependency major versions.                                                                                                                                                                                                                 |
| **3.8**                       | ⚠️ Maintenance Only | Requires older, pinned versions of dependencies (e.g., `pendulum` v2, `urllib3` v1) to function. **Python 3.8 has reached end-of-life (EOL) and support will be deprecated in a future release.** Python 3.8 is supported because this is the system Python on our Emerson Ovation EDS server. |

### Important Notes on Conditional Dependencies

To maintain compatibility across this range, **Poetry** automatically pins several major dependencies based on your Python version, ensuring maximum stability.

- **Python 3.9+ (Recommended)**: Installations on Python 3.9 and newer automatically receive the latest, feature-rich major versions of core libraries such as `keyring`, `pendulum`, `urllib3`, and the development tools `pytest` and `pytest-cov`.
    
- **Python 3.8 (Legacy)**: If you install on Python 3.8, you will receive older, but still compatible and secure, versions of the following packages:
    
    - `keyring` (`^24.3`)
    - `pendulum` (`^2.1.2`)
    - `urllib3` (`^1.26.19`)
    - `uvicorn` (`^0.33.0`)
    - `mysql-connector-python` (`^8.3.0`)
        
### Recommended Version

**Python 3.11 or newer is highly recommended** for the best performance, security, and access to the latest features from all third-party libraries. If you are using the Developer Setup, please target Python 3.11.9 as specified in the getting started guide.

---

## Comparison: `pipeline-eds` Python Package vs Emerson Ovation EDS Excel Add-In vs EDS Portal Webapp

### **1. Emerson Ovation EDS Excel Add-In**

**Pros:**

* Integrates directly into Excel, a familiar environment for many users.
* Supports creating tabular trends and exporting EDS data within spreadsheets.
* Good for ad-hoc data analysis if you are comfortable with Excel.
* **Insert Tabular Trend** functionality is diversified from the **EDS Excel Function library** (`EDS point fields`, `EDS archives`, `EDS steam tables`, `EDS tabular trends`)

**Cons:**

* The interface for generating data (e.g., via **Insert tabular trend**) is **cumbersome and not very intuitive**.
* Users must manually insert charts after data extraction unless they have a pre-built spreadsheet template.
* Requires Excel to be installed.
* Requires **admin rights to install an MSI package** provided by Emerson, which can be a barrier in locked-down environments.
* Not scriptable or easily automated unless the user is comortbale calling XLSX files from Task Scheduler.
* Limited performance for rapid exploration or querying.


### **2. Emerson EDS Portal Webapp**

**Pros:**

* Web-based, no local installation required.
* Intuitive UI for browsing EDS data.
* Good for **interactive, point-and-click exploration**.
* Tab-building allows for excellent stable page-based system analysis, so the inqueries do not need to be repeated.

**Cons:**

* To visualize **one-off sensor curves**, you must:

  * Open the filter utility.
  * Manually type in the full IESS (sensor ID).
  * Adjust time ranges via multiple clicks.
* Limited ability to automate or integrate data retrieval into other workflows.
* Data export is usually manual.
* Requires a web browser and network access.


### **3. `pipeline-eds` Python Package**

**Pros:**

* **CLI-based**, enabling extremely **fast visualization of one-off sensor curves** with simple commands.
* No GUI overhead: you just run a command like `pipeline trend ABC XYZ --start 2024-01-01 --end 2024-01-31` and get results quickly.
* Supports automation and scripting for repetitive or scheduled data extraction and processing.
* Minimal installation requirements: only needs a shell environment (PowerShell, Bash).
* Works on platforms where Excel or full web browsers may not be available.
* Can be used on **mobile devices** through tools like Termux on Android, avoiding the need for Emerson’s paid mobile app license.
* Open-source, so you can extend or customize the tool.
* Integrates easily with Python-based data workflows, dashboards, or analytics tools.

**Cons:**

* Requires familiarity with command-line interfaces and scripting (though the Termux shortcuts widget allows mobile users to not use the terminal directly.)
* No graphical input UI (yet) for those who prefer point-and-click.
* May require initial setup and learning curve if you are not familiar with Python or CLI tools.

---

### **4. Mobile Use Case**

* **Emerson Mobile Apps** (iOS and Android) require additional licensing and purchase from Emerson.
* `pipeline-eds` can be run on mobile devices using:

  * **Termux** (Android) or similar terminal emulators.
  * Any SSH client connected to a remote system with the package installed.
* This approach **undercuts the need for Emerson’s mobile app license**, providing a lightweight, free way to query and visualize EDS data on the go.
* Great for field engineers or operators needing quick access to sensor data without carrying a laptop or paying for extra licenses.

---

### **Software Comparison Summary Table**

| Feature                         | Excel Add-In                           | EDS Portal Webapp                  | `pipeline-eds` Python Package                       |
| ------------------------------- | -------------------------------------- | ---------------------------------- | --------------------------------------------------- |
| Installation                    | Requires MSI installer + Excel         | No install, web browser only       | Python package + shell (PowerShell/Bash)            |
| Ease of Use                     | Familiar Excel UI, but clunky workflow | Intuitive GUI, but slow multi-step | CLI-based, fast but requires command-line skills    |
| Automation                      | No                                     | No                                 | Yes, fully scriptable                               |
| Speed for One-off Sensor Curves | Slow, manual chart creation            | Slow, many clicks to filter        | Fast, one command                                   |
| Integration with other tools    | Limited                                | Limited                            | Excellent, can be embedded in Python pipelines      |
| Mobile Access                   | No                                     | Web browser only (no offline)      | Possible via Termux or SSH, no extra license needed |
| Licensing Cost                  | Included with Emerson tools            | Included with Emerson tools        | Open-source, free                                   |

---

### Software Comparison Final Thoughts

If you mainly need **quick, interactive visualizations occasionally**, and prefer GUIs, the `Excel Add-In` or `Portal` may suffice.

If you want **fast, automated, scriptable access**, with the flexibility to integrate into broader workflows — especially **for repeated sensor curve visualizations** — `pipeline-eds` is much more efficient.

If **mobile access without extra license costs** is important, `pipeline-eds` on Termux or similar CLI apps is a strong advantage.


---

## 📝 Final Note on Naming
The project is internally referred to as `pipeline`, but the PyPI package is named `pipeline-eds` to avoid a name conflict with an existing, unrelated package on PyPI. For CLI usage, the pyproject.toml file creates aliases so you can use `pipeline`, `eds`, and `pipeline-eds` interchangeably in your terminal. This allows for a more intuitive command-line experience without the need to use the full PyPI package name.
