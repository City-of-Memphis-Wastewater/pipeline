# src/pipeline/api/eds/soap/demo.py
from __future__ import annotations # Delays annotation evaluation, allowing modern 3.10+ type syntax and forward references in older Python versions 3.8 and 3.9
import logging

logger = logging.getLogger(__name__)

from pipeline.decorators import log_function_call
from pipeline.api.eds.soap.client import EdsSoapClient

@log_function_call(level=logging.DEBUG)
def demo_eds_soap_api_tabular():

    EdsSoapClient.soap_api_iess_request_tabular(plant_name = "Stiles",idcs = ['I-0300A','I-0301A'])
    EdsSoapClient.soap_api_iess_request_tabular(plant_name = "Maxson",idcs = ['FI8001','M310LI'])
    
if __name__ == "__main__":

    '''
    - auto id current function name. solution: decorator, @log_function_call
    - print only which vars succeed
    '''
    import sys
    from pipeline.logging_setup import setup_logging

    cmd = sys.argv[1] if len(sys.argv) > 1 else "default"

    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("CLI started")

    if cmd == "demo_soap_tabular":
        demo_eds_soap_api_tabular()

    else:
        print("Usage options: \n" 
        "poetry run python -m pipeline.api.eds.soap.demo demo_soap_tabular"
        )