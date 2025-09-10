# mulch/reg_winreg.py
import os
from pathlib import Path
import platform
if platform.system() == "Windows":
    import winreg

local_app_data = Path(os.environ['LOCALAPPDATA'])
mulch_dir = local_app_data / 'mulch'
mulch_dir.mkdir(parents=True, exist_ok=True)
call_script_mulch_workspace = mulch_dir / "call-mulch-workspace.ps1"
call_script_mulch_seed = mulch_dir / "call-mulch-seed.ps1"
icon_path = r"%LOCALAPPDATA%\mulch\mulch-icon.ico"

# Helper to delete a key tree safely
def delete_key_tree(root, sub_key):
    try:
        with winreg.OpenKey(root, sub_key, 0, winreg.KEY_READ | winreg.KEY_WRITE) as key:
            # Recursively delete subkeys
            i = 0
            while True:
                try:
                    sub = winreg.EnumKey(key, i)
                    delete_key_tree(key, sub)
                except OSError:
                    break
                i += 1
        winreg.DeleteKey(root, sub_key)
    except FileNotFoundError:
        pass  # Key doesn't exist, that's fine

# Helper to create a shell entry
def create_shell_entry(base_key, menu_key_path, display_name, command, icon=None, position="Top", command_flags=0):
    # Create the main shell key
    with winreg.CreateKey(base_key, menu_key_path) as key:
        winreg.SetValueEx(key, '', 0, winreg.REG_SZ, display_name)
        if icon:
            winreg.SetValueEx(key, "Icon", 0, winreg.REG_SZ, icon)
        winreg.SetValueEx(key, "Position", 0, winreg.REG_SZ, position)
        winreg.SetValueEx(key, "CommandFlags", 0, winreg.REG_DWORD, command_flags)

    # Create the command subkey
    with winreg.CreateKey(base_key, f"{menu_key_path}\\command") as cmd_key:
        winreg.SetValueEx(cmd_key, '', 0, winreg.REG_SZ, command)

def verify_registry():
    base = winreg.HKEY_CURRENT_USER
    classes_key = r"Software\Classes"

    required_keys = [
        r"Directory\Background\shell\mulch_workspace\command",
        r"Directory\shell\mulch_workspace\command",
        r"Directory\Background\shell\mulch_seed\command",
        r"Directory\shell\mulch_seed\command"
    ]

    missing = []
    for k in required_keys:
        try:
            with winreg.OpenKey(base, classes_key + "\\" + k, 0, winreg.KEY_READ):
                pass
        except FileNotFoundError:
            missing.append(k)

    if missing:
        raise RuntimeError(f"Registry keys missing after installation: {missing}")


def call():
    # Base key for current user classes
    base = winreg.HKEY_CURRENT_USER
    classes_key = r"Software\Classes"

    # Paths to remove if they exist
    keys_to_remove = [
        r"Directory\Background\shell\mulch_workspace",
        r"Directory\shell\mulch_workspace",
        r"Directory\Background\shell\mulch_seed",
        r"Directory\shell\mulch_seed",
    ]

    # Remove existing entries
    for k in keys_to_remove:
        delete_key_tree(winreg.OpenKey(base, classes_key, 0, winreg.KEY_WRITE), k)

    # Background right-click, mulch workspace
    background_command = f'powershell.exe -NoProfile -ExecutionPolicy Bypass -File "{call_script_mulch_workspace}" "%V"'
    create_shell_entry(
                    base_key=winreg.OpenKey(base, classes_key, 0, winreg.KEY_WRITE),
                    menu_key_path=r"Directory\Background\shell\mulch_workspace",
                    display_name='mulch workspace',
                    command = background_command,
                    icon=icon_path)

    # Folder right-click, mulch workspace
    folder_command = f'powershell.exe -NoProfile -ExecutionPolicy Bypass -File "{call_script_mulch_workspace}" "%L"'
    create_shell_entry(
                    base_key = winreg.OpenKey(base, classes_key, 0, winreg.KEY_WRITE),
                    menu_key_path=r"Directory\shell\mulch_workspace",
                    display_name='mulch workspace',
                    command=folder_command,
                    icon=icon_path)
    
    # Background right-click, mulch seed
    background_command = f'powershell.exe -NoProfile -ExecutionPolicy Bypass -File "{call_script_mulch_seed}" "%V"'
    create_shell_entry(
                    base_key=winreg.OpenKey(base, classes_key, 0, winreg.KEY_WRITE),
                    menu_key_path=r"Directory\Background\shell\mulch_seed",
                    display_name='mulch seed',
                    command = background_command,
                    icon=icon_path)

    # Folder right-click, mulch seed
    folder_command = f'powershell.exe -NoProfile -ExecutionPolicy Bypass -File "{call_script_mulch_seed}" "%L"'
    create_shell_entry(
                    base_key = winreg.OpenKey(base, classes_key, 0, winreg.KEY_WRITE),
                    menu_key_path=r"Directory\shell\mulch_seed",
                    display_name='mulch seed',
                    command=folder_command,
                    icon=icon_path)

    print("Registry context menu entries removed and recreated successfully!")
