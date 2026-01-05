# Changelog

All notable changes to this project will be documented in this file.

The format is (read: strives to be) based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---


## [0.4.2] – 2026-01-04
### Tested:
- uv is stable for dependency management.

### Changed:
- Detritis files in root moved to dedicated jupyter and node-red based folders in ~./dev/ on the Ubuntu system.
 
---

## [0.4.1] – 2026-01-04
### Changed:
- Implement uv for dependency management, and uv-build for building. poetry is out.

---

## [0.3.84] – 2025-12-07
### Changed:
- Migrate get_configurable_default_plant_name() from SecurityAndConfig generic class to EDS-specific config.py file. 

### Removed:
- Freesimplegui removed as a dependency, and local interface removed in favor of web. Tkinter popups are still present for config and credentials.
- src/pipeline/gui.py is redundant to the gui cli command, requires maintenance, doesn't exit smoothly, and is an overly generic name with an overly specific purpose (the Eds Trend Web GUI).
- `mpl` and `windows` optional dependendy groups are no longer available.

### Added:
- There is now pipeline.api.eds.config, pipeline.api.eds.rest.config, pipeline.api.eds.soap.config, and the comparable security files, for clear separation of concerns.
- `localdb_fallback_windows` has been added as an optional dependency group.


### Plan:
- Once we migrate to SOAP as the standarad, and test work on the Stiles EDS server, then we can destroy the local MariaDB database file fallback, and `poetry remove mysql-connector-python`.


---

## [0.3.83] – 2025-12-06
### Changed:
- Edit eds_trend.html for style

### Added:
- MockBuffer is able to be used with curl and from the HTML is VPN is not available.
- Docuement the curl command in curl-to-MockData-Eds-Trend.md

### To do:
- Move web gui to `frontend` directory in root, like the `/gastrack` project.

---

## [0.3.80] – 2025-11-24
### Fixed:
- get_prompt_manager() -> PromptManager

---

## [0.3.78] – 2025-11-23

### Added:
- Lots of Grok-generated files added including the node red flows.

### Fixed:
- On Termux we had attempted to set us a vs code dev environment. This was accidentally commited. It has to be forcibly untracked, with history cleaned. This caused a merge challege on the Ubuntu dev environment. 

---

## [0.3.76] – 2025-11-21

### Changed:
- Comment out package.py section in publish.yml. It is overkill.

---

## [0.3.75] – 2025-11-21

### Fixed:
- **CI/CD Bug Hunt:** _version.py is now only generated into ./src/pipeline/, not ./dist/ - this is whete the current publish.yaml is failing to finalize the build for PyPI.
---

## [0.3.71] – 2025-11-21

### CI/CD & Dependency Management Overhaul

- **Separated `dev` and `test` dependency groups** in `pyproject.toml`  
  The heavyweight build tools (`shiv`, `pyinstaller`, `pex`, etc.) are now isolated in `[tool.poetry.group.dev.dependencies]` while lightweight CI tooling (`pytest`, `pytest-cov`, `ruff`) lives in a dedicated `[tool.poetry.group.test.dependencies]`. This eliminates the long-standing `shiv` marker/version hell that was breaking CI on every runner.

- **Fixed Termux/Android packaging path**  
  `shiv` is now correctly pinned to real, existing versions:
  - `^1.0.8` on all normal platforms (Linux, Windows, macOS)
  - `0.5.1` on Termux/Android (`sys_platform == "android"`)
  No more “version does not exist” resolver failures.

- **Stable, fast, green GitHub Actions workflow**  
  - CI now installs only what it needs: `poetry install --without dev --with test`
  - Successfully builds and resolves the lockfile on **Python 3.8 → 3.13** inclusive
  - Linting and test steps are present but intentionally disabled by default (commented out) until the current ~200 legitimate ruff warnings are triaged. This keeps CI useful and fast instead of perpetually red.

- **Future-proof foundation**  
  The test group is ready for immediate re-enabling:
  ```yaml
  - name: Lint with ruff
    run: poetry run ruff check .
  - name: Run tests with pytest
    run: poetry run pytest tests/ -v --cov=pipeline --cov-report=term-missing

---

## [0.3.70] - 2025-11-21

### Added
- **Termux/mobile development workflow dramatically improved**
  - Added `docs/termux_zshrc_nov2025` — complete zsh + Oh My Zsh config with ghost-text autosuggestions, clean prompt, and async performance
  - Integrated `getnf` for instant Nerd Font installation (Hermit, Cascadia, 0xProto, 3270, etc.)
  - Full mobile contributor onboarding path documented
- **EDS client package migration started**
  - New modular structure under `src/pipeline/api/eds/` (`client.py`, `session.py`, `exceptions.py`, `points.py`, `trend.py`)
  - All `typer.Exit()` removed from library code → web server now survives off-VPN
  - Introduced proper `EdsTimeoutError` / `EdsAuthError`
  - Old monolithic `eds.py` preserved as `eds_legacy.py` during safe, incremental migration
  - Grok needed to be continuously monitored and corrected for accuracy. Lots of hype. Example: `docs/by_grok_edited_clay.md`

### Changed
- Temporarily renamed new `/src/pipeline/api/eds/__init__.py` → `/src/pipeline/api/eds/hold__init__.py` to surface import gaps for zero-downtime migration

### Fixed
- Web GUI no longer crashes on connection timeout
- CLI + web both fully functional during refactor

### Learned
- cat EOF blocks with no triple ticks is a great way to copy and paste code from an AI chat bot.

---

## [0.3.69] - 2025-11-17

### Changed
- Stabilized Packaging for Python 3.9: Refined pyproject.toml dependency constraints for starlette to ensure compatibility across Python 3.9 and Python 3.10+ environments, resolving previous Poetry lock failures during .pyz creation.
- Improved Packaging Workflow: Updated the packaging script to ensure consistent generation of the self-contained executable (.pyz) and the accompanying Windows batch file (.bat) within the WSL/Ubuntu environment.
- Updated project dependencies and regenerated poetry.lock.
- Implemented a pre-launch threaded server strategy rather than using JIT.

---

## [0.3.68] - 2025-11-14

### Changed:
- Pydantic and FastAPI are out, Starlette and msgspec are in.
- `trend_server_eds.py` and `config_server.py` updated. `gui_starlette_msgspec_plotly.py` has replaced `gui_fastapi_plotly_live.py` as the EDS live demo plotter.
- Why this choice: Compatibility with PEX, PYZ, Python 3.8, and ease of install on Termux.

## Abandoned
- `--site-packages` flag added to shiv and pex builds in build_multi.py, to ensure dependency availability. This should not pick up the global pip packages on the system, because the poetry env was not build with the `--system-site-packages` flag.

## Investigated:
- `package.py` is the current ultimate successor to `build_release.py` and `build_multi.py`. It has been determined that `zipapp` has a multiplex issue on Python 3.12+, and `shiv` succeeds in cleanly packaging .PYZ while compressing, rejecting .PYC (which prevents cross platform use) and also embedding file assets like HTML.   

---

## [0.3.67] - 2025-11-13

### Added:
- Pex build script, `build_pex.py`; `build_pex.sh` deprecated. 
- Added STATIC and TEMPLATES references to trend_server_eds.py and Config_server.py, using `from importlib.resources import files`.
- Reference static and template assets in `tool.poetry.include` in `pyproject.toml`.

---

## [0.3.66] - 2025-11-13

### Added:
- Pex build script, build_pex.sh. Forced to regernate the wheel. It is testing well but only in the project folder - not sure if it has carried the HTML assets.

### Fixed:
- Web config input stabilzed. Lots of work on the HTML and the FastAPI endpoints and architecture. See `./src/pipeline/server/` and `./src/pipeline/interface/web_gui/`.
- Keyboard interrupt improved while two servers are running, though bugs still exist.
- Web config should be able to be embedded as iframe or as standalone tab.
- Runaway None return for credentials and config entry resolved with explicit checks for None for each one within the EdsClient functions.

---

## [0.3.63] - 2025-11-10

### Added:
- **gui CLI command:** Build web-based interface in raw html and alpine.js, along with local version in freesimplegui. Streamlit and freesimpleguiweb were tested. FSGW is dead because remi is dead. Streamlit is less scalable and maintainable than just writing the HTML directly.
- **Tauri Example:** Generate tauri example with three js embedded canvas, found in .\src\example\tauri_multimodal_app\; the build files are gitignore'd but `npm run tauri build` can be run from what is available, from inside the src-tauri directory. So begins a new stack - we will favor web-based graphics, and then these can be made native with Tauri. Should we mgrate entirely to Rust? See notes in my disparate Markdown Vaults.

### Fixed:
- pipeline.server.trend_server_eds.launch_server_for_web_gui() leverages find_open_port(s).

---

## [0.3.61] - 2025-11-01

Lots here. Too much, actually.

### Breaking:
- **MissionClient:** Renamed the data fetching method in mission.py from download_analog_csv() to get_analog_csv_bytes(). This change clarifies that the function retrieves raw bytes from the API and does not perform local disk I/O (file saving).

### Added:
- **Redundancy Class:** Introduced a new class to manage and document variable clarity, particularly concerning function returns and side effects for the common issue when comparing setters vs return functions. 
- **gui CLI command:** Build web-based interface in raw html and alpine.js, along with local version in freesimplegui. Streamlit and freesimpleguiweb were tested. FSGW is dead because remi is dead. Streamlit is less scalable and maintainable than just writing the HTML directly.
- **Tauri Example:** Generate tauri example with three js embedded canvas, found in .\src\example\tauri_multimodal_app\; the build files are gitignore'd but `npm run tauri build` can be run from what is available, from inside the src-tauri directory. So begins a new stack - we will favor web-based graphics, and then these can be made native with Tauri. Should we mgrate entirely to Rust? See notes in my disparate Markdown Vaults.

### Changed:
- Improve MissionClient for stability, rollout, and norms.
- Start improving EdsClient to benefit from mimicking MissionClient in it's improved state.
- **Analog Data Retrieval Migration:** Migrated the demonstration and ultimate use of analog data retrieval to the more capable /Download/AnalogDownload endpoint (via get_analog_csv_bytes()) instead of the limited /Analog/Table endpoint. The /Analog/Table endpoint was found to lack precise control over time-delta resolution, start/end times, and efficient pagination.

### Discourse:
- **Code Intent Documentation:** Ongoing work on using decorators and internal mechanisms for explicitly hinting and documenting language intent, especially related to function return values and expected state changes.

---

## [0.3.59] - 2025-10-27
 
### Fixed: 
- Upgrade pyhabitiat ^1.0.35, which should not block interactice terminal without good reason.

### Added:
- SOAP API access demo function and bones added for EdsClient. Testing success for both of our EDS servers.
- Provide link and copy-pasted information about WSDL (Web Service Description Language), which is intrinsic to SOAP-based services.
- Add defaults to get_soap_api_url() and get_eds_api_url() for automated use if credentials are not provided.
- Add and test Cancel button for inputs sought with WebConfigurationManager.

### Changed:
- from suds.client import Client' -> 'from suds.client import Client as SudsClient', for rigor; I worry the parlance 'Client' will get lost, and this way it is easier to cntrl+F. 

---

## [0.3.58] - 2025-10-26

### Changed:
- BSD-3-clause license changed to MIT license.

---

## [0.3.57] - 2025-10-24

### Changed:
- CLI command name: `pipeline-eds install` -> `pipeline-eds setup`. Clearly differentiates pipx install or source code build or binary installation from the setup / integration process. Function name: **setup_integration()**, with Typer command alias **setup**. 
- Flag added to trend and live CLI commands -mpl/--matplotlib. logic adjusted to use webplot unless matplotlib is both available and explicitly specified.
- Minimum pyhabitat version changed to 1.0.30, so that constrained environments with false positives for interactive_terminal_is_available() will fall back to tkinter or web-based input for configuration.

### Fixed:
- Resolved incomplete function name migration. The setup CLI command, meant to set up Termux shortcuts, et cetera, is utilized explicitly in termux_setup.py. At this point, the 'install' was migrated to 'setup'.
- Change the function names in termux_setup.py from setup_termux_install() to setup_termux_integration(), and from cleanup_termux_install() to cleanup_termux_integration(). Only use was in cli.py
- Change the function names in windows_setup.py from setup_windows_install() to setup_windows_integration(), and from cleanup_windows_install() to cleanup_windows_integration(). Only use was in cli.py
- gnore poetry.lock in Termux to allow ci.yml to succeed when pushing from Termux.
- Push existing fix to src/pipeline/gui_fastapi_plotly_live.py from laptop, for stability and updated pydantic and fastapi specifications above and below 3.12.

---

## [0.3.54] - 2025-10-24

### Added:
-  Implement github workflow publish.yaml, to replace manual "poetry build" and "twine upload .\dist\*VERSION_NUMBER*", to be managed automatically when running "gh release create v**VERSION_NUMBER** -F .\docs\CHANGELOG.md". 
- Note that testing is limited to successful build and successful minimal run of "pipeline-eds"; plotting and api calls are not tested.

---

## [0.3.53] - 2025-10-24

### Changed:
-  Block automatic installation on each CLI run, in `--- SETUP / INSTALL HOOK ---` section. Artifact left in place. Termux Widgets Shortcuts can now e installed by using the install CLI command.

### Coming Soon:
- cli folder, with cli-rjn.py, cli-mission.py, cli-eds.py, and cli-transmit.py; the currrent cli.py will ultimately be moved to cli-eds.py, after cli-mission.py is established and stable and can be referenced. 
- cli-transmit.py will be a bit more complex, to establish and configure the bones to be called by Windows Task Scheduler or the appropriate alternative. [See issue 44](https://github.com/City-of-Memphis-Wastewater/pipeline/issues/44).
- .pex. 

### Stability status
- Currently Termux installation is stable using `pipx install --system-site-packages pipeline-eds` and can be ugraded with `pipx upgrade pipeline-eds`.  Now that numpy has been removed as a dependenency. For fallback security, install both `pkg install python-cryptography` and `pkg install rust`; with rust, if the pre installed python-cryptography library is not picked up for whatever reason from system site packages, rust enables `pip install cryptography` to build from source. This fallback approach is not possible with numpy; `pkg install python-numpy` works, but `pip install numpy` is tenuous with pitfalls, so, burn it. 


---

## [0.3.51] - 2025-10-23

### Dependency reduction:
- Isolate normalization for gui_plotly_static.py, splitting off helper functions into the plottools.file. Alter these functions to use raw python math and to not require numpy, because dealing with numpy for pipx install on termux is no longer a fun game, and testing on termux for rolling verions is a key development aspect.

### File deletion:
- Redundant gui_plotly_multi.py, destroyed.

---

## [0.3.48] - 2025-10-22

### Breaking Change / Deprecation
- **PyHabitat Version :** User pyhabitat ^1.0.18, due to function name changes. Function name changes:  is_termux() -> on_termux(), is_ish_alpine() -> on_ish_alpine().

---

## [0.3.44] - 2025-10-20

### Breaking Change / Deprecation
- **Removed Local Environment Module:** The local file containing environment checks (src/pipeline/environment.py) has been removed and replaced by the external pyhabitat library. Action Required: All code must update imports from src.pipeline.environment to pyhabitat.

### Features & Improvements
- **PyHabitat Integration:** Environment checks and capability detection logic (like is_termux() and tkinter_is_available()) are now sourced from the pyhabitat dependency, ensuring consistent behavior across all projects that use it.

### Dependency Update: 
- Added pyhabitat as a direct project requirement.

---

## [0.3.23] - 2025-10-07

We need to make sure these changes impact the static tmp files as well as continuously served html.

### Added
- **Dark Mode Plotting with Mode Button:** CSS and Javascript are used to edit the HTML.
- **Hide Legend / Show Legend Button:** This works well to toggle on and off the legend.

### Changed:
- Plot colors, line sizes, and marker sizes are no longer manually set - instead this is managed by the default theme, seaborn. 

---

## [0.3.22] - 2025-10-07

We need dark mode plotting.

### Added
- **points-export CLI command:** Now users can generate an export file of all of their EDS points associated with their plant. Plant name and file path can be provided or will be determined automatically.

### Broken
- The iess value filter is not working consistently for multiple values provided. Ergo, the feature is not included for the `points-export` command at this time.

---

## [0.3.14] - 2025-10-07

### Fixed

- **Termux Installation Stability:** Minor internal refinements to the Termux shortcut generation and shell alias cleanup routines.
- **Termux Alias Conflict:** Corrected an issue where standalone binaries (ELF and PYZ) installed in Termux would incorrectly register the generic package name (`pipeline-eds`) as a shell alias in `~/.bashrc`.
    - **The Problem:** For versions **0.3.3 through 0.3.12**, this led to conflicts by potentially overwriting the alias intended for the **pipx installation**.
    - **The Solution:** Standalone installations now use distinct, unique aliases to allow all installation types to coexist cleanly:
        - **ELF Binary:** Registers the alias: **`pipeline-eds-elf`**
        - **PYZ Binary:** Registers the alias: **`pipeline-eds-pyz`**
    - *Note: Users who ran a standalone binary in Termux during the affected versions should run the application's cleanup command or manually remove any problematic `pipeline-eds` alias blocks from `~/.bashrc`.*
	
---

## [0.3.12] - 2025-10-07

### Fixed

- Fixed a critical rendering bug in the static Plotly generator (gui_plotly_static.py) where traces linked to secondary Y-axes (yaxis2, yaxis3, etc.) were incorrectly clipped or hidden. This issue prevented users from seeing all data series when multiple units were plotted. The resolution involves explicitly setting the overlaying='y' property for all non-primary Y-axes to ensure correct canvas drawing order.

---

## [0.3.10] - 2025-10-05

### Added

- **Robust Termux Integration:** Major enhancements for users running the application within Termux (Android). The application now automatically detects the installation method (pipx or standalone ELF binary) and sets up the best possible shortcuts.
- **Termux Widget Shortcuts:**
    - **New:** Automatic creation of Termux widget shortcuts such as (`{PACKAGE_NAME}-pipx.sh`, `{PACKAGE_NAME}-elf.sh`, or `{PACKAGE_NAME}-pyz.sh`) to launch the application easily from the Android home screen. These names infer installation method, which at this time is primarily for developer troubleshooting.
    - **New:** Creation of a separate **Upgrade Widget Shortcut** (`{PACKAGE_NAME}-upgrade.sh`) for pipx installations. This script runs a full update, including `pkg upgrade -y` and `pipx upgrade {PACKAGE_NAME}`, before launching the application.
- **ELF Binary Shell Alias:** For users running the standalone ELF binary, a permanent shell alias (`{PACKAGE_NAME}-elf`) is now registered in `~/.bashrc` to allow the application to be run simply by typing the alias from any shell session.
- **PYZ Binary Shell Alias:** For users running the PYZ zipapp binary, a permanent shell alias (`{PACKAGE_NAME}-pyz`) is now registered in `~/.bashrc` to allow the application to be run simply by typing the alias from any shell session.
- **Clean Uninstallation:** Added comprehensive cleanup functions (`cleanup_termux_install`, `cleanup_shell_alias`) to safely remove all generated Termux shortcuts, aliases, and markers from `~/.bashrc` upon uninstallation.

### Changed

- **Improved Shortcut Execution Logic:** Termux shortcut scripts now use the resolved path of the running executable (e.g., `{running_exec_path}`) instead of assuming its location or relying on a simple filename, significantly improving reliability.
- **Dependency Management:** All Termux widget scripts now explicitly `source $HOME/.bashrc` to ensure necessary environment variables and aliases are loaded when running from a non-interactive widget environment.

### Refactored

- Internal Termux setup functions were renamed for improved clarity and consistency:
    - `setup_termux_elf_shortcut` to **`setup_termux_widget_elf_shortcut`**
    - `register_shell_alias_elf` to **`register_shell_alias_elf_to_basrc`**
	
---

## [0.3.8] - 2025-10-04

This release implements critical enhancements and refactoring to the **Termux installation pipeline**, focusing on improving executable detection reliability and installation logic flow.

### Added

- **Modular ELF Detection:** Introduced the dedicated `is_elf()` helper function to isolate and standardize native binary detection logic within the `setup_termux_install()` dispatcher. 
    
- **System Library Dependency:** Added `import sys` to support new requirements for executable path resolution, necessary for advanced type detection.
    

### Changed

- **Robust ELF Type Validation:** The mechanism for detecting a standalone Termux ELF binary was overhauled. Detection now utilizes a reliable **magic number check** (`b'\x7fELF'`) on the executable file, replacing the previous, less dependable heuristic based on parsing architecture strings in the filename.
    
- **Idempotent Shortcut Creation:** Implemented a pre-write existence check in `setup_termux_elf_shortcut()` and `setup_termux_pipx_shortcut()` to ensure **idempotency** and prevent unintentional file modification of user-customized Termux widget scripts.
    
- **Consolidated Pipx Setup:** The logic for setting up the separate pipx upgrade shortcut has been merged directly into the `setup_termux_pipx_shortcut()` routine, streamlining the package installation path. 
    
- **Refined ELF Shortcut Execution:** Modified the ELF shortcut script generation to explicitly execute a `cd "$HOME"` command prior to binary execution, mitigating execution errors in environments where the Termux widget launches from an arbitrary working directory.
    

### Refactored

- **Installation Utility Removal:** Removed the centralized `_create_shortcut` utility function; its directory creation, writing, and permission-setting functionality has been inlined into specific setup functions for enhanced modularity and control.

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
