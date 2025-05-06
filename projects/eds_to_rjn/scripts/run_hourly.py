#run_hourly.py
import sys
from projects.eds_to_rjn.scripts.daemon_runner import run_hourly_cycle, run_hourly_cycle_manual

def cli():
    
    cmd = sys.argv[1] if len(sys.argv) > 1 else "default"

    if cmd == "default-file":
        run_hourly_cycle()
    elif cmd == "select-filepath-and-overwrite":
        run_hourly_cycle_manual()
    else:
        print("Usage options: \n" 
        "poetry run python -m projects.eds_to_rjn.scripts.run_hourly default-file \n"  
        "poetry run python -m projects.eds_to_rjn.scripts.run_hourly select-filepath-and-overwrite")

if __name__ == "__main__":
    #run_hourly_cycle()
    cli()


