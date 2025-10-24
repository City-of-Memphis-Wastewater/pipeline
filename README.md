# `pipeline-eds`

`pipeline-eds` is a Python project designed to simplify API access to Emerson Enterprise Data Server (EDS) machines. It facilitates seamless data exchange between Emerson's Ovation EDS system and various external parties, including third-party contractors and internal employees. The project is distributed on PyPI under the package name `pipeline-eds`.

---

## ⚡Quick Start

For detailed installation and usage instructions, see [QUICKSTART.md](https://github.com/City-of-Memphis-Wastewater/pipeline/blob/main/QUICKSTART.md).  
This guide includes step-by-step commands for Windows, Linux, Termux, and developer setups.


---

## 🚀 Getting Started

This detailed guide provides instructions for installing and running `pipeline-eds`. To ensure you follow the right path, first choose the method that best fits your needs.

---

### Choosing Your Installation Method

  * **For the absolute simplest setup (No Python required):** If you want to run the tool without installing Python or managing dependencies, use a pre-built binary. Follow **Method 1: Using Pre-Built Binaries**.
  * **For an easy CLI setup with simple updates:** If you are comfortable with the command line and want to easily keep the tool updated, `pipx` is the recommended approach. Follow **Method 2: CLI Installation with `pipx`**.
  * **For developing and contributing to the project:** If you plan to modify the source code, you need a full development environment. Follow **Method 3: Developer Setup with Poetry**.
  * **For installing from a Git clone without Poetry (Advanced):** If you have cloned the repository and need to install dependencies manually with `pip`, follow **Method 4: Installing from a Git Clone with `pip`**.

-----

<details>
<summary> Method 1: Using Pre-Built Binaries (`.exe`, `.elf`, `.pyz`)</summary>

This is the easiest way to get started, especially on systems where you don't have Python installed. These are standalone packages that you can download and run directly.

1.  **Download the appropriate binary** for your system from the project's [**GitHub Releases page**](https://github.com/City-of-Memphis-Wastewater/pipeline/releases).

    - `pipeline-eds*.exe`: For Windows.
    - `pipeline-eds* (ELF has no extension)`: For Linux and Termux on Android.
    - `pipeline-eds*.pyz`: A zipapp for any system that has Python installed.

2.  **Place the file** in a convenient location.
	```bash
	# On Termux (Android)
	termux-setup-storage
	cp storage/downloads/ . to copy the file from your Android downloads folder to your $HOME folder
	```
	On iSH, you launch by default in the `root` directory, and the executable can be copied here (if you would like) manually using the file browser.

3.  **Run the command** from your terminal. You may need to make the `.elf` file executable first (`chmod +x pipeline-eds-*`).

    ```bash
    # On Windows
    .\pipeline-eds-*.exe config

    # On Linux or Termux
    ./pipeline-eds-* config
    ```

For more details on the pros and cons of each binary type, see the **Distribution and Packaging** section below.

</details>

-----

<details>
<summary> Method 2: CLI Installation with `pipx` (Recommended for CLI Users)</summary>

`pipx` installs and runs Python applications in isolated environments. This is the best way to get easy updates and avoid conflicts with other Python packages.

**1. Install Python and `pip`**

If you don't have them, install them using your system's package manager or an official installer.
> **Windows Note:** If installing from the `.exe` installer from [python.org](https://www.python.org/downloads/), be sure to check the box for **"Add Python to PATH"** during setup.

```bash
# On Windows (using a package manager in PowerShell)
winget install Python.Python.3.11
# Or with Chocolatey:
# choco install python

# On Ubuntu/Debian
sudo apt update && sudo apt install python3 python3-pip python-is-python3

# On Termux (Android)
pkg update && pkg install python
pkg install python python-cryptography python-numpy

# Some of these are likely overkill given prepackaged cryptography, but I want you to succeed, and I will continue testing.
pkg install clang make libffi openssl-dev libffi-dev
# pkg install rust # probably not necessary, with `python-cryptography` installed

# On Alpine (iSH on iOS)
apk update && apk add python3 py3-pip
apk add py3-cryptography py3-numpy py3-virtualenv
apk add openssl-dev libffi-dev
```

**2. Install `pipx`**

Use `pip` to install `pipx` and add its scripts to your system's PATH.

```bash
python3 -m pip install --user pipx
python3 -m pipx ensurepath
```

*(You may need to restart your terminal for the PATH change to take effect.)*

**3. Install `pipeline-eds`**

Install the package from PyPI using `pipx`.

```bash
# For all systems (Linux, macOS, Windows)
pipx install pipeline-eds

# For Termux and iSH, which require dedicated system site packages like py3-cryptography
pipx install --system-site-packages pipeline-eds

# For Windows users who want database features from the pyodbc library (the usefulness of this has not yet been developed).
pipx install "pipeline-eds[windows]"

# If you want non-browser plotting with Matplotlib (Linux, macOS, Windows)
pipx install "pipeline-eds[mpl]"
# With the `trend` command, use the `--webplot` flag to direct the plot to plotly HTML anyways and circumvent Matplotlib.
```

**4. Run Commands**

You can now use the `eds` alias directly in your terminal. There is also the `pipeline` alias and the `pipeline-eds` alias.

```bash
eds config
eds trend M100FI --start June3 --end June17
```

</details>

-----
<details>
<summary> Method 3: Developer Setup with Poetry</summary>

This method is for contributors who need a full development environment to modify the source code.
Learn more about [git](https://www.youtube.com/watch?v=qrD3z9_9DXU).
See [git guide](https://git-scm.com/docs).

**1. Clone the Repository**

```bash
git clone https://github.com/City-of-Memphis-Wastewater/pipeline.git
cd pipeline
```

**2. Install `pyenv` and `Poetry`**

This project uses `pyenv` to manage Python versions and `Poetry` for dependency management.
You do not need `pyenv`.
This project is compatible with Python 3.8 to 3.14, so there's not a huge demand for your to dial in a specific version.

  * **`pyenv`:** Follow the official installation guide for your OS ([pyenv](https://github.com/pyenv/pyenv) for Linux/macOS, [pyenv-win](https://github.com/pyenv-win/pyenv-win) for Windows).
  * **`Poetry`:** Follow the official [Poetry installation guide](https://www.google.com/search?q=https://python-poetry.org/docs/%23installation).

**3. Configure the Project Environment**

If you so choose.

```bash
pyenv install 3.11.9
pyenv local 3.11.9
poetry env use 3.11.9
```

**4. Install Dependencies**

Yes, this part is entirely necessary.

```bash
poetry install
```

**5. Run Commands**

Execute all commands with `poetry run`. The `[tool.poetry.scripts]` section in `pyproject.toml` allows `eds` to work as an alias for `python -m pipeline.cli`.

```bash
poetry run eds config
poetry run eds ping
```

</details>

-----

<details>
<summary> Method 4: Installing from a Git Clone with `pip` (Advanced)</summary>

This method is for users who have cloned the repository but prefer to manage the environment with `pip` and `venv`. This is often necessary on platforms like **Termux** or **iSH (Alpine)**.
A use-case for this is for generating binaries on a system such that it is compatible with that system (Note that **iSH** emulates x86_64).

**1. Clone the Repository**

If you haven't already, clone the project from GitHub.

```bash
git clone https://github.com/City-of-Memphis-Wastewater/pipeline.git
cd pipeline
```

**2. Export Dependencies to `requirements.txt`**

This project's dependencies are in `pyproject.toml` and I have tried to export as necessary to the `requirements.txt` file. 
The `requirements.txt` is availible in the root of the package.
But, if you need to update the `requirements.txt` file, you can though on another system because `poetry` is unavailable on Termux.

```bash
# Install poetry if you don't have it
pip install poetry
# Export the requirements file
poetry export -f requirements.txt --output requirements.txt --without-hashes
# You can now uninstall poetry if you wish
# pip uninstall poetry
```

**3. Install System Dependencies and Create a Virtual Environment**

The steps below are platform-specific.

#### For Termux (Android)

1.  **Install System Build Dependencies:**
    ```bash
    pkg update && pkg upgrade -y
	pkg install python python-cryptography # python-numpy # numpy is no longer needed as of 0.3.50
    
	# The build tools (rust, clang, etc.) are generally not needed IF the 
    # Termux-installed packages satisfy the requirements.
    # The below line can likely be removed if --system-site-packages is used, 
    # but we will leave it for max compatibility.
    pkg install rust clang make openssl-dev libffi-dev
	pip install --no-cache-dir cryptography
    ```
2.  **Create and Activate a Virtual Environment:**
    ```bash
	# CRITICAL: Use the --system-site-packages flag to access Termux's pre-compiled packages.
    python -m venv --system-site-packages .venv
    source .venv/bin/activate
    ```
3.  **Install Python Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Run Commands:**
    ```bash
    python -m pipeline.cli config
    ```

#### For iSH / Alpine Linux (iOS)

1.  **Install System Build Dependencies:**
    ```bash
    apk update
	
	# Install the core Python environment tools and essential pre-compiled Python libraries
    # Installing 'py3-cryptography' and 'py3-numpy' via apk avoids difficult, lengthy compilation from source later.
    apk add python3 py3-pip py3-cryptography py3-numpy py3-virtualenv
    apk add gcc musl-dev build-base openssl-dev libffi-dev 
    
	```
2.  **Create and Activate a Virtual Environment:**
    ```bash
	# The '--system-site-packages' flag is crucial: it allows this venv to access the
    # pre-compiled Python packages (like py3-cryptography) installed in the previous step 
    # by the system package manager (apk). This satisfies their requirements without re-installing.
	python3 -m venv --system-site-packages .venv
    
	# Activate the virtual environment
	source .venv/bin/activate
    ```
3.  **Install Python Dependencies:**
    ```bash
	# Install all project-specific dependencies defined in the requirements file.
    # 'pip' will install these packages into the isolated '.venv', while still
    # using the system packages (if needed) due to the venv's configuration.
    pip install -r requirements.txt
    ```
4.  **Run Commands:**
    ```bash
	 # Execute the main application command using the Python interpreter from the activated venv.
    python3 -m pipeline.cli trend M100FI
	
	# Deactivate the virtual environment. This resets the shell's PATH to the system's 
    # default Python environment.
    deactivate
    
    # NOTE: If you run the software after deactivating, the 'python3' command will only see
    # system-installed libraries, not the packages installed specifically for this project.
    # You can reactivate the environment anytime using 'source .venv/bin/activate' if you are 
    # in the project's directory.
    ```
	
</details>

---

<details>
<summary>📦 Distribution and Packaging</summary>

This project supports multiple packaging formats to make installation flexible across platforms.  
While some formats allow installation on systems without internet access, note that the **application itself requires internet connectivity** to call its API.

[How to Build Binaries](https://github.com/City-of-Memphis-Wastewater/pipeline/wiki/Build-Scripts,-How-and-Where)

### 🔹 Executables (`.exe`, `.elf`)
- **Generated by**: [`build_executable.py`](https://github.com/City-of-Memphis-Wastewater/pipeline/blob/main/build_executable.py)
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
- **Generated by**: [`build_shiv.sh`](https://github.com/City-of-Memphis-Wastewater/pipeline/blob/main/build_shiv.py) on WSL2 Ubuntu
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

</details>

---

## ✨ Tips for Optimal Usage & Maintenance
To ensure a smooth and efficient experience with `pipeline-eds`, consider the following best practices:

### Keep `pipeline-eds` Updated: 
Regularly upgrade your `pipeline-eds` installation to benefit from the latest features, bug fixes, and performance improvements.
```bash
pipx upgrade pipeline-eds
```

### Understanding eds config and Credential Management:
The first time you execute a command requiring access to your EDS API (e.g., eds trend), `pipeline-eds` will guide you through a one-time configuration process. Your sensitive API credentials (URL, username, password) are securely stored using your operating system's native keyring service. This avoids storing plaintext passwords. If your credentials change, you can re-run eds config at any time to update them.

### Network Connectivity (VPN Essential):
If your EDS server is located on a private network (e.g., within your organization's internal network), you must be connected to the appropriate Virtual Private Network (VPN). Failure to do so will result in connection errors when `pipeline-eds` attempts to fetch data.

### Leveraging Flexible Date/Time Inputs:
The `eds trend` command offers highly flexible date and time parsing for its --start and --end options, thanks to the `pendulum` package. You can use a wide variety of natural language inputs, such as:

- `--start "2023-09-18"`
- `--start "Sept 18"`
- `--end "now"` 

Experiment with different formats to suit your query needs. Remember to use quotes around values if they contain spaces.

---


## ⚙️ Project Implementation & Use Cases

Aside from being a CLI tool for visualing sensor data at will, `pipeline` is designed to be deployed as a scheduled task on a Windows server, for hourly data transmission to a third party.

  * The project is executed by **Windows Task Scheduler**, which calls a PowerShell script (`main_eds_to_rjn_quiet.ps1`) as the entry point.
  * The iterative timing (e.g., hourly execution) is handled by the `Task Scheduler`, not by Python.
  * For these automated tasks, a standard `venv` is used, as `Task Scheduler` can run under different user accounts.

---

## 📱 Running on Android (`Termux`)

The `pipeline` project can be installed and run on Android devices using the **[Termux](https://termux.dev/)** terminal emulator.  
For most users, **CLI installation via `pipx` is the recommended method**, as development is not expected in this environment and `pipx` provides the smoothest way to stay up to date.

### Termux Installation Options

There are several ways to run `pipeline` inside Termux, depending on your needs:

- **`pipx` (Recommended)**  
  - Provides rolling updates and integrates with the Termux home‑screen widget.  
  - As of **v0.3.8**, you `eds install` will generate a **shortcut button** in the Termux widget to update `pipeline-eds` without needing to open the terminal.  
  - Requires Python and `pipx` to be installed.  
  - Best choice if you want to keep up with frequent changes.

- **Native ELF Binary**  
  - A prebuilt `.elf` binary is available specifically for Termux.  
  - Smoothest rollout for users who just want the CLI tool without expecting updates.

- **`.pyz` Zipapp**  
  - ⚠️ Known limitation: launching `.pyz` directly from the Termux `.shortcuts` widget may trigger a **permission error**.

---


### 🌐 Termux and Web-Based Visuals (Plotly)
When using `pipeline-eds` in Termux to generate plots (e.g., with `eds trend`), the visuals are displayed as web-based HTML pages using libraries like Plotly. Instead of directly opening a graphical window (which is not typically supported by Termux's command-line environment), `pipeline-eds` serves these HTML files via a local web server (often on localhost).

[Why localhost](https://github.com/City-of-Memphis-Wastewater/pipeline/wiki/Why-localhost-on-Termux)

---

<details>
<summary> 🐍 Python Version Compatibility</summary>

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

</details>

---

[Comparing the pipeline-eds Python Package to the Emerson Ovation EDS Excel Add-In and the EDS Portal Webapp](https://github.com/City-of-Memphis-Wastewater/pipeline/wiki/Comparison-of-%60pipeline%E2%80%90eds%60-Python-Package-vs-Emerson-Ovation-EDS-Excel-Add%E2%80%90In-vs-EDS-Portal-Webapp)

---

## 📝 Final Note on Naming
The project is internally referred to as `pipeline`, but the PyPI package is named `pipeline-eds` to avoid a name conflict with an existing, unrelated package on PyPI. For CLI usage, the pyproject.toml file creates aliases so you can use `pipeline`, `eds`, and `pipeline-eds` interchangeably in your terminal. This allows for a more intuitive command-line experience without the need to use the full PyPI package name.



