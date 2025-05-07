import subprocess
from pathlib import Path
def main():
    script_path = Path.home() / "setup_termux.sh"
    if script_path.exists():
        subprocess.run(["chmod","+x",str(script_path)], check = True)
        subprocess.run(["bash",str(script_path)], check = True)
    else:
        print(f"{script_path} not found.")
