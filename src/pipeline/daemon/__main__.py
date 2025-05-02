# pipeline/daemon/__main__.py

import argparse
from pipeline.daemon.controller import start_daemon, stop_daemon, status_daemon  # Example functions

def main():
    parser = argparse.ArgumentParser(description="Control the pipeline daemon.")
    parser.add_argument("-start", action="store_true", help="Start the daemon")
    parser.add_argument("-stop", action="store_true", help="Stop the daemon")
    parser.add_argument("-status", action="store_true", help="Check daemon status")

    args = parser.parse_args()

    if args.start:
        start_daemon()
    elif args.stop:
        stop_daemon()
    elif args.status:
        status_daemon()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
