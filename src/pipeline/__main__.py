# pipeline/__main__.py

# Example of __main__.py or your CLI's main function

from pipeline.server.server_manager import ServerManager
from pipeline.server.web_utils import launch_server_for_web_gui_
# Import your specific Starlette app instances
from src.pipeline.server.trend_server_eds import app as trend_app
from src.pipeline.server.config_server import app as config_app 
# ... other apps

def launch_all_services():
    manager = ServerManager()

    # Launch the Trend GUI Server
    trend_server, trend_thread = launch_server_for_web_gui_(trend_app, port=8082)
    manager.register_server(trend_server, trend_thread)
    
    # Launch the Config Input Server
    config_server, config_thread = launch_server_for_web_gui_(config_app, port=8083)
    manager.register_server(config_server, config_thread)

    # Launch browser for initial page (e.g., trend GUI)
    # launch_browser("http://127.0.0.1:8082") 
    
    # Start the blocking central loop
    manager.run_main_loop()

if __name__ == "__main__":
    launch_all_services()