import platform
import sys
from pathlib import Path
import os

try:
    import distro  # external package, best for Linux detection
except ImportError:
    distro = None


class SystemInfo:
    """Detects the current OS, distro, and version information."""

    def __init__(self):
        self.system = platform.system()  # "Windows", "Linux", "Darwin"
        self.release = platform.release()
        self.version = platform.version()
        self.architecture = platform.machine()

    def detect_linux_distro(self) -> dict:
        """Return Linux distribution info (if available)."""
        if self.system != "Linux":
            return {}

        if distro:
            return {
                "id": distro.id(),
                "name": distro.name(),
                "version": distro.version(),
                "like": distro.like(),
            }
        else:
            # fallback to /etc/os-release parsing
            os_release = Path("/etc/os-release")
            if os_release.exists():
                info = {}
                for line in os_release.read_text().splitlines():
                    if "=" in line:
                        k, v = line.split("=", 1)
                        info[k.strip()] = v.strip().strip('"')
                return {
                    "id": info.get("ID"),
                    "name": info.get("NAME"),
                    "version": info.get("VERSION_ID"),
                    "like": info.get("ID_LIKE"),
                }
            return {"id": "unknown", "name": "unknown", "version": "unknown"}

    def detect_android_termux(self) -> bool:
        if "ANDROID_ROOT" in os.environ or "TERMUX_VERSION" in os.environ:
            return True
        if "android" in self.release.lower():
            return True
        return False
    
    def get_os_tag(self) -> str:
        """Return a compact string for use in filenames (e.g. ubuntu22.04)."""
        if self.system == "Windows":
            win_ver = platform.win32_ver()[0] or "windows"
            return f"windows{win_ver}"

        if self.system == "Darwin":
            mac_ver = platform.mac_ver()[0].split(".")[0] or "macos"
            return f"macos{mac_ver}"

        if self.system == "Linux":
            if self.detect_android_termux():
                return "android"

            info = self.detect_linux_distro()
            distro_id = info.get("id") or "linux"
            distro_ver = (info.get("version") or "").replace(".", "")
            if distro_ver:
                return f"{distro_id}{info['version']}"
            return distro_id

        return self.system.lower()
    
    def to_dict(self) -> dict:
        """Return a full snapshot of system information."""
        info = {
            "system": self.system,
            "release": self.release,
            "version": self.version,
            "arch": self.architecture,
            "os_tag": self.get_os_tag(),
        }
        if self.system == "Linux" and self.detect_android_termux():
            info["id"] = "android"
            info["name"] = "Android (Termux)"
        elif self.system == "Linux":
            info.update(self.detect_linux_distro())
        elif self.system == "Windows":
            info["win_version"] = platform.win32_ver()
        elif self.system == "Darwin":
            info["mac_ver"] = platform.mac_ver()[0]
        return info

    def pretty_print(self):
        """Nicely formatted printout of system info."""
        info = self.to_dict()
        print("--- System Information ---")
        for k, v in info.items():
            print(f"{k:10}: {v}")


if __name__ == "__main__":
    sysinfo = SystemInfo()
    sysinfo.pretty_print()
    print(f"sysinfo.system = {sysinfo.system}")
    print(f"sysinfo.release = {sysinfo.release}")
    print(f"sysinfo.version = {sysinfo.version}")
    print(f"sysinfo.architecture = {sysinfo.architecture}")
