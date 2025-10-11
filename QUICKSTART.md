## **`pipeline-eds` Quickstart Cheat Sheet**

---

### **1️⃣ Windows (Fastest: pipx)**

```powershell
# Install Python 3.11 if not installed (winget or choco)
winget install Python.Python.3.11

# Install pipx
python -m pip install --user pipx
python -m pipx ensurepath
# Restart terminal if necessary

# Install pipeline-eds
pipx install pipeline-eds

# Run commands
eds config          # first-time credential setup
eds ping            # test connection
eds trend M100FI --start 2025-10-01 --end 2025-10-10
```

💡 Optional: Use `[windows]` extras if you want pyodbc support (not yet fully developed).

---

### **2️⃣ Linux (Ubuntu/Debian, Fastest: pipx)**

```bash
# Install Python 3 and pip
sudo apt update && sudo apt install python3 python3-pip python-is-python3 -y

# Install pipx
python3 -m pip install --user pipx
python3 -m pipx ensurepath
# Restart shell

# Install pipeline-eds
pipx install pipeline-eds

# Run commands
eds config
eds ping
eds trend M100FI --start 2025-10-01 --end 2025-10-10
```

---

### **3️⃣ Termux (Android) – Recommended: pipx with widget support**

```bash
# Update packages
pkg update && pkg upgrade -y
pkg install python python-cryptography python-numpy -y

# Install pipx
python -m pip install --user pipx
python -m pipx ensurepath
# Restart Termux

# Install pipeline-eds
pipx install --system-site-packages pipeline-eds

# Run commands
eds config
eds ping
eds trend M100FI --start 2025-10-01 --end 2025-10-10

# Optional: Update later via Termux widget shortcut
eds install --upgrade
```

💡 Tip: `eds trend` will generate Plotly HTML plots. Open with `termux-open <filename>` or the localhost URL printed in the terminal.

---

### **4️⃣ iSH / Alpine Linux (iOS)**

```bash
# Install core packages
apk update
apk add python3 py3-pip py3-cryptography py3-numpy gcc musl-dev build-base openssl-dev libffi-dev -y

# Create virtual environment using system site packages
python3 -m venv --system-site-packages .venv
source .venv/bin/activate

# Install pipeline-eds from requirements.txt (if cloned) or PyPI
pip install pipeline-eds   # or pip install -r requirements.txt

# Run commands
python3 -m pipeline.cli config
python3 -m pipeline.cli ping
python3 -m pipeline.cli trend M100FI --start 2025-10-01 --end 2025-10-10

# Deactivate when done
deactivate
```

💡 Tip: Plotly HTML output opens in Safari using `open <file>` if Termux/iSH supports it. Otherwise, copy the localhost URL to the browser.

---

### **5️⃣ Optional: Pre-built Binaries (Windows / Linux / Termux)**

Available at [**GitHub Releases page**](https://github.com/City-of-Memphis-Wastewater/pipeline/releases)
- .pyz ⬇️🐍
- .exe ⬇️🪟
- ELF Binaries ⬇️📱🐧🍎


```bash
# Make executable if needed (Linux/Termux)
chmod +x pipeline-eds-*

# Run directly
./pipeline-eds-* config
./pipeline-eds-* trend M100FI --start 2025-10-01 --end 2025-10-10
```

#### Key:
- 🐍: Requires Python on the system (but not dependencies)
- ⬇️: Download the file, or transfer the file via cable or USB.
- 🪟: Windows
- 📱: Mobile
- 🐧: Linux
- 🍎: Apple

---

### **Tips**

* Always connect to VPN if EDS is on a private network.
* First-time `eds config` saves credentials securely via OS keyring.
* Use quotes for date strings if using natural language formats:

  ```bash
  --start "Sept 18" --end "now"
  ```
* `pipx` installations are easiest to update:

  ```bash
  pipx upgrade pipeline-eds
  ```

