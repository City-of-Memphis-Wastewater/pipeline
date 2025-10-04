# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---


## [0.2.115] - 2025-10-04

This release focuses on significant improvements to the **Windows Installation and Setup** process, providing a more professional, silent, and integrated user experience for standalone executable users.

### Added

- **Silent Installation Logging (Windows):** Implemented file-based logging to `install_log.txt` within the `AppData` configuration directory. All verbose setup output is now redirected from `stdout` to this file, ensuring a non-disruptive, single-line console status message during application launch.
    
- **Start Menu Shortcut:** Automated creation of a launcher `.BAT` file in the user's Start Menu Programs directory (`%APPDATA%\Microsoft\Windows\Start Menu\Programs`), significantly improving application accessibility.
    
- **Comprehensive Uninstall/Cleanup (Windows):** Introduced `cleanup_windows_install()` and supporting routines to reliably remove all generated installation artifacts (Desktop launcher, Start Menu shortcut, Context Menu Registry keys, and AppData installation files) upon request.
    

### Changed

- **Installation Dispatcher Optimization (Windows):** Implemented version-based installation tracking using an `install_version.txt` file in AppData. This prevents all setup routines (registry, shortcuts) from re-running on every application launch, eliminating startup overhead.
    
- **Context Menu Information:** The `setup_info_eds.ps1` PowerShell script, accessible via the folder background right-click, is now dynamically populated to explicitly reference the executable type (`.EXE` or `.PYZ`) and includes the definitive link to the GitHub Releases page for direct download options.
    

### Fixed

- **Excessive Setup Output:** Resolved the issue where verbose installation details were printed to the console during every application startup by implementing the version-based state check and redirecting all setup messages to the log file.

---

## [0.2.113] - 2025-10-04

This release focuses on a major overhaul of the build and packaging system to improve reliability, cross-platform compatibility, and maintainability.

### Added

-   **New Python-based Build System:** Introduced a new `build_shiv.py` script to orchestrate the creation of the `shiv` executable. Continue to rely on the `build_shiv.sh` until further notice.
-   **Enhanced Artifact Naming:** Executable (`.EXE` and `ELF`) filenames are now more descriptive, dynamically including the package name, version, Python version, OS, and architecture. Zipapp/Shiv (`.pyz`) filenames inclue package version and python version but not yet the OS or the architecture.
-   **Docker Containerization:** Added mult-dev, dev, and production containers to Github Packages.
-   **Releases**: PyZ and binary distribution for cross-platform execution: https://github.com/City-of-Memphis-Wastewater/pipeline/releases/tag/v0.2.112

### Changed

-   **Build Script Migration:** Replaced the `build_shiv.sh` shell script with the more robust `build_shiv.py` script. This removes dependencies on shell-specific tools like `grep`, `awk`, and `unzip`.
-   **Standardized Wheel-based Builds:** The build process now exclusively creates a Python wheel (`.whl`) first and uses it as the sole source for the `shiv` executable. This ensures consistency and correctly handles the project's `src`-layout.
-   **Decoupled Metadata Extraction:** The build script now extracts package metadata (name, version) directly from the generated wheel's `METADATA` file, removing the need for the build script to import the application code.

### Removed

-   **Legacy Shell Script:** The `build_shiv.sh` file has been removed.
-   **Unreliable Source Directory Builds:** Removed the fragile fallback logic that attempted to build the `shiv` executable directly from the source directory, which was a source of runtime errors.

### Fixed

-   **Runtime `AttributeError`:** Resolved a critical runtime error (`AttributeError: module 'pipeline' has no attribute 'cli'`) that occurred on systems without the full development toolchain. The fix was to enforce a clean, wheel-based build that correctly packages the `pipeline` module.
-   **Cross-Platform Build Inconsistencies:** The new build system eliminates inconsistencies between different build environments (e.g., Poetry vs. non-Poetry, Windows vs. Linux (Termux, Ubuntu, MX23)).
-   **Termux Installation**: Termux-native `ELF` file `pipeline-eds-0.2.112-py312-android-aarch64` is the best for smooth rollout to Android devices. 

### Learned
-    **Termux Quirk**: Termux Widget `.shortcuts/` shell scripts hit a permission-denied wall when referencing a `.PYZ` zipapp.

---

## [0.2.112] - 2025-10-03
- Added Windows/Ubuntu/Android executables
- Updated dependencies (plotly, uvicorn, pendulum)
- Minor bug fixes in CLI commands

---

## [0.2.111] - 2025-10-02
- Initial multi-OS release with `.whl`, `.pyz`, and `.exe` distributions
- Refactored `pipeline.cli` for better CLI alias support

### Changed
- Updated Python dependency pins for 3.8–3.14 compatibility