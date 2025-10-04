import platform
import sys
from pathlib import Path

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

    def to_dict(self) -> dict:
        """Return a full snapshot of system information."""
        info = {
            "system": self.system,
            "release": self.release,
            "version": self.version,
            "arch": self.architecture,
        }
        if self.system == "Linux":
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
    print(sysinfo.system)
    print(sysinfo.release)
    print(sysinfo.version)
    print(sysinfo.architecture)
