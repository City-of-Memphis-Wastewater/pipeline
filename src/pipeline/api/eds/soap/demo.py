# src/pipeline/api/eds/soap/demo.py
from __future__ import annotations # Delays annotation evaluation, allowing modern 3.10+ type syntax and forward references in older Python versions 3.8 and 3.9
import logging

logger = logging.getLogger(__name__)

from pipeline.decorators import log_function_call
from pipeline.api.eds.soap.client import EdsSoapClient

@log_function_call(level=logging.DEBUG)
def demo_eds_soap_api_tabular():
    # Prioritized plant list — it will try them in order until one succeeds
    plants_to_try = [
        ("Maxson",  ['FI8001', 'M310LI', 'FI7065', 'FI7080']),     # currently online
        ("Stiles",  ['I-0300A', 'I-0301A', 'I-5005A']),            # when you're on Stiles network
    ]

    success = False
    for plant_name, idcs in plants_to_try:
        print(f"\nTrying {plant_name} plant...")
        try:
            result = EdsSoapClient.soap_api_iess_request_tabular(
                plant_name=plant_name,
                idcs=idcs
            )
            if result is not None:  # tabular request succeeded
                success = True
                print(f"\n{plant_name} PLANT CONNECTED AND TREND DATA SUCCESSFULLY RETRIEVED!")
                break
        except Exception as e:
            print(f"{plant_name} failed → {e}")
            continue

    if not success:
        print("\nAll configured plants failed. Check your network/VPN.")

@log_function_call(level=logging.DEBUG)
def demo_eds_soap_api_tabular_classic():

    EdsSoapClient.soap_api_iess_request_tabular(plant_name = "Stiles",idcs = ['I-0300A','I-0301A'])
    #EdsSoapClient.soap_api_iess_request_tabular(plant_name = "Maxson",idcs = ['FI8001','M310LI'])
    
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
    elif cmd == "demo_soap_tabular_classic":
        demo_eds_soap_api_tabular_classic()

    else:
        print("Usage options: \n" 
        "poetry run python -m pipeline.api.eds.soap.demo demo_soap_tabular \n"
        "poetry run python -m pipeline.api.eds.soap.demo demo_soap_tabular_classic"
        )