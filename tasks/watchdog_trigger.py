# tasks/watchdog_trigger.py

import sys
import os
#sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'projects')))
# Adjust sys.path to point to the root of the project, not src/
#project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))  # Two levels up
#src_path = os.path.join(project_root, 'src')  # Assuming 'src' is at the root level
#sys.path.append(src_path)  # Add 'src' directory to the path
#sys.path.append(project_root)


from pipeline.daemon.watchdog import check_and_restart_if_needed


if __name__ == "__main__":
    check_and_restart_if_needed()


