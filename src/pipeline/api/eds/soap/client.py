from __future__ import annotations # Delays annotation evaluation, allowing modern 3.10+ type syntax and forward references in older Python versions 3.8 and 3.9import time
import sys
import logging
import time
from suds.client import Client as SudsClient # uses suds-py3

from pipeline.api.eds.rest.client import EdsRestClient
from pipeline.security_and_config import SecurityAndConfig, get_base_url_config_with_prompt
from pipeline.variable_clarity import Redundancy
class EdsSoapClient:
    def __init__(self):
        pass

    # --- Context Management (Pattern 2) ---
    def __enter__(self):
        """Called upon entering the 'with' block."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Called upon exiting the 'with' block (for cleanup)."""
          
        # Logout from SOAP (if login was performed)
        if self.authstring:
            print(f"[{self.plant_name}] Attempting SOAP logout...")
            try:
                # We need a SOAP client instance to perform the logout
                if self.soapclient is None:
                    # Initialize just to logout, if not done already
                    self.soapclient = SudsClient(self.soap_url)
                self.soapclient.service.logout(self.authstring)
                print(f"[{self.plant_name}] Logout successful.")
            except Exception as e:
                print(f"[{self.plant_name}] Error during SOAP logout: {e}")
                
        # Return False to propagate exceptions, or True to suppress them
        return False
    @classmethod
    @Redundancy.set_on_return_hint(recipient=None,attribute_name="tabular_data")
    def soap_api_iess_request_tabular(cls, plant_name: str | None= None, idcs: list[str] | None = None):
        
        from pipeline.api.eds.soap.config import get_eds_soap_api_url
        from pipeline.api.eds.config import get_service_name

        tabular_data = None
        soapclient = None
        authstring = None
        
        use_default_idcs = True
        if plant_name is None:
            plant_name = SecurityAndConfig.get_configurable_default_plant_name()
        print(f"plant_name = {plant_name}")
        service_name = get_service_name(plant_name = plant_name) # for secure credentials
    
        if idcs is None:
            if use_default_idcs:
                idcs = SecurityAndConfig.get_configurable_idcs_list(plant_name)
            else:
                idcs = SecurityAndConfig.get_temporary_input()
        
        base_url = get_base_url_config_with_prompt(service_name = f"{plant_name}_eds_base_url", prompt_message=f"Enter {plant_name} EDS base url (e.g., http://000.00.0.000, or just 000.00.0.000)")
        if base_url is None: return
        eds_soap_api_port = SecurityAndConfig.get_config_with_prompt(config_key = f"{plant_name}_eds_soap_api_port", prompt_message=f"Enter {plant_name} EDS SOAP API port (e.g., 43080)")
        if eds_soap_api_port is None: return
        eds_soap_api_sub_path = SecurityAndConfig.get_config_with_prompt(config_key = f"{plant_name}_eds_soap_api_sub_path", prompt_message=f"Enter {plant_name} EDS SOAP API WSDL PATH (e.g., 'eds.wsdl')")
        if eds_soap_api_sub_path is None: return
        username = SecurityAndConfig.get_credential_with_prompt(service_name, "username", f"Enter your EDS API username for {plant_name} (e.g. admin)", hide=False)
        if username is None: return
        password = SecurityAndConfig.get_credential_with_prompt(service_name, "password", f"Enter your EDS API password for {plant_name} (e.g. '')")
        if password is None: return
        idcs_to_iess_suffix = SecurityAndConfig.get_config_with_prompt(f"{plant_name}_eds_api_iess_suffix", f"Enter iess suffix for {plant_name} (e.g., .UNIT0@NET0)")
        if idcs_to_iess_suffix is None: return
        
        #session = EdsRestClient.login_to_session_with_api_credentials(api_credentials)
        
        eds_soap_api_url = get_eds_soap_api_url(base_url = base_url, 
                                                eds_soap_api_port = eds_soap_api_port, 
                                                eds_soap_api_sub_path = eds_soap_api_sub_path)
        if eds_soap_api_url is None:
            logging.info("Not enough information provided to build: eds_soap_api_url.")
            logging.info("Please rerun your last command or try something else.")
            return
        try:
            # 1. Create the SOAP client
            print(f"Attempting to connect to WSDL at: {eds_soap_api_url}")
            soapclient = SudsClient(eds_soap_api_url)
            print("SOAP client created successfully.")
            # You can uncomment the line below to see all available services
            # print(soapclient)

            # 2. Login to get the authstring
            # This is the "authstring assignment" you asked for.
            print(f"Logging in as user: '{username}'...")
            authstring = soapclient.service.login(username, password)
            
            if not authstring:
                print("Login failed. Received an empty authstring.")
                return

            print(f"Login successful. Received authstring: {authstring}")

            # 3. Use the authstring to make other API calls
            
            # Example 1: ping (to keep authstring valid)
            print("\n--- Example 1: Pinging server ---")
            soapclient.service.ping(authstring)
            print("Ping successful.")

            # Example 2: getServerTime
            print("\n--- Example 2: Requesting server time ---")
            server_time_response = soapclient.service.getServerTime(authstring)
            print("Received server time response:")
            print(server_time_response)

            # Example 3: getServerStatus
            print("\n--- Example 3: Requesting server status ---")
            server_status_response = soapclient.service.getServerStatus(authstring)
            print("Received server status response:")
            print(server_status_response)
            
            # --- NEW EXAMPLES BASED ON YOUR CSV DATA ---

            # Example 4: Get a specific point by IESS name
            # We will use 'I-0300A.UNIT1@NET1' from your latest output
            print("\n--- Example 4: Requesting point by IESS name ('{}') ---")
            try:
                # Create a PointFilter object
                point_filter_iess = soapclient.factory.create('PointFilter')
                
                # Set the iessRe (IESS regular expression) filter
                # We use the exact name, but it also accepts wildcards
                
                idcs = [s.upper() for s in idcs]
                iess_list = [x+idcs_to_iess_suffix for x in idcs]
                for iess in iess_list:
                    point_filter_iess.iessRe = iess
                    
                    # Call getPoints(authstring, filter, order, startIdx, maxCount)
                    # We set order, startIdx, and maxCount to None
                    points_response_iess = soapclient.service.getPoints(authstring, point_filter_iess, None, None, None)
                    print("Received getPoints response (by IESS):")
                    print(points_response_iess)

            except Exception as e:
                print(f"Error during getPoints (by IESS): {e}")

            # -----------------------------------------------

            # Example 6: Request Tabular (Trend) Data
            # This will request historical data for 'I-0300A.UNIT1@NET1'
            print("\n--- Example 6: Requesting tabular data for 'I-0300A.UNIT1@NET1' ---")
            request_id = None # Initialize request_id
            try:
                # 1. Define time range (e.g., last 10 minutes)
                end_time = int(time.time())
                start_time = end_time - 600 # 600 seconds = 10 minutes
                
                print(f"Requesting data from {start_time} to {end_time}")

                # 2. Create the main TabularRequest object (see PDF page 32)
                tab_request = soapclient.factory.create('TabularRequest')

                # 3. Create and set the time period
                period = soapclient.factory.create('TimePeriod')
                # Use getattr() for 'from' as it's a Python keyword
                getattr(period, 'from').second = start_time
                period.till.second = end_time
                tab_request.period = period
                
                # 4. Set the step (e.g., one value every 60 seconds)
                tab_request.step = soapclient.factory.create('TimeDuration')
                tab_request.step.seconds = 60
                
                # 5. Create a request item for the point
                item = soapclient.factory.create('TabularRequestItem')
                item.pointId = soapclient.factory.create('PointId')
                item.pointId.iess = 'I-0300A.UNIT1@NET1' # Using point from Example 4
                
                # 6. Set the function (e.g., 'AVG', 'RAW', 'MIN', 'MAX')
                # 'AVG' gives averages. Use 'RAW' to get raw recorded samples.
                item.function = 'AVG'
                
                # 7. Add the item to the request
                tab_request.items.append(item)

                # 8. Send the request
                print("Submitting tabular data request...")
                request_id = soapclient.service.requestTabular(authstring, tab_request)
                print(f"Request submitted. Got request_id: {request_id}")

                # 9. Poll for request status (see PDF page 30)
                status = None
                max_retries = 10
                retries = 0
                while status != 'REQUEST-SUCCESS' and retries < max_retries:
                    retries += 1
                    time.sleep(1) # Wait 1 second before checking
                    status_response = soapclient.service.getRequestStatus(authstring, request_id)
                    status = status_response.status
                    print(f"Polling status (Attempt {retries}): {status}")

                    if status == 'REQUEST-FAILURE':
                        print(f"Request failed: {status_response.message}")
                        break
                
                # 10. Get the data if successful (see PDF page 40)
                if status == 'REQUEST-SUCCESS':
                    print("Request successful. Fetching data...")
                    tabular_data = soapclient.service.getTabular(authstring, request_id)
                    print("Received tabular data:")
                    print(tabular_data)
                else:
                    print(f"Failed to get tabular data after {max_retries} retries.")

            except Exception as e:
                print(f"Error during tabular data request: {e}")
                # If the request was made but failed mid-poll, try to drop it
                if request_id and authstring and soapclient:
                    try:
                        print(f"Attempting to drop request {request_id} after error...")
                        soapclient.service.dropRequest(authstring, request_id)
                        print(f"Dropped request {request_id}.")
                    except Exception as drop_e:
                        print(f"Error trying to drop request {request_id}: {drop_e}")


        except Exception as e:
            from pipeline.api.eds.exceptions import connection_error_message
            connection_error_message(e, url = eds_soap_api_url)
            
        finally:
            
            # Removed diagram close logic
            
            # 5. Logout using the authstring
            if authstring and soapclient:
                print(f"\nLogging out with authstring: {authstring}...")
                try:
                    soapclient.service.logout(authstring)
                    print("Logout successful.")
                except Exception as e:
                    print(f"Error during logout: {e}")
            else:
                print("\nSkipping logout (was not logged in).")

        return tabular_data
    
    @staticmethod
    def soap_api_iess_request_single(plant_name: str|None, idcs:list[str]|None):

        from pipeline.api.eds.soap.config import get_eds_soap_api_url
        from pipeline.api.eds.config import get_service_name
        # --- Initialize vars ---
        soapclient = None
        authstring = None
        
        # --- Get encrypted credentials and plaintext configuration values --- 
        if plant_name is None:
            plant_name = SecurityAndConfig.get_configurable_default_plant_name()

        service_name = get_service_name(plant_name = plant_name) # for secure credentials
        base_url = get_base_url_config_with_prompt(service_name=f"{plant_name}_eds_base_url", prompt_message=f"Enter {plant_name} EDS base url (e.g., http://000.00.0.000, or just 000.00.0.000)")
        if base_url is None: return
        username = SecurityAndConfig.get_credential_with_prompt(service_name, "username", f"Enter your EDS API username for {plant_name} (e.g. admin)", hide=False)
        if username is None: return
        password = SecurityAndConfig.get_credential_with_prompt(service_name, "password", f"Enter your EDS API password for {plant_name} (e.g. '')")
        if password is None: return
        idcs_to_iess_suffix = SecurityAndConfig.get_config_with_prompt(f"{plant_name}_eds_api_iess_suffix", f"Enter iess suffix for {plant_name} (e.g., .UNIT0@NET0)")
        if idcs_to_iess_suffix is None: return
        
        # Let API Port and the sub path be None, such that the defaults will be used.
        eds_soap_api_url = get_eds_soap_api_url(base_url = base_url)
        if eds_soap_api_url is None:
            logging.info("Not enough information provided to build: eds_soap_api_url.")
            logging.info("Please rerun your last command or try something else.")
            sys.exit()

        try:
            # 1. Create the SOAP client
            print(f"Attempting to connect to WSDL at: {eds_soap_api_url}")
            soapclient = SudsClient(eds_soap_api_url)
            print("SOAP client created successfully.")
            # You can uncomment the line below to see all available services
            # print(soapclient)

            # 2. Login to get the authstring
            # This is the "authstring assignment" you asked for.
            print(f"Logging in as user: '{username}'...")
            authstring = soapclient.service.login(username, password)
            
            if not authstring:
                print("Login failed. Received an empty authstring.")
                return

            print(f"Login successful. Received authstring: {authstring}")

            # 3. Use the authstring to make other API calls
            
            # Example 1: ping (to keep authstring valid)
            print("\n--- Example 1: Pinging server ---")
            soapclient.service.ping(authstring)
            print("Ping successful.")

            # Example 2: getServerTime
            print("\n--- Example 2: Requesting server time ---")
            server_time_response = soapclient.service.getServerTime(authstring)
            print("Received server time response:")
            print(server_time_response)

            # Example 3: getServerStatus
            print("\n--- Example 3: Requesting server status ---")
            server_status_response = soapclient.service.getServerStatus(authstring)
            print("Received server status response:")
            print(server_status_response)
            
            # --- EXAMPLES OF  CSV DATA ---

            # Example 4: Get a specific point by IESS name
            # We will use 'I-0300A.UNIT1@NET1' from your CSV
            ## WWTF,I-0300A,I-0300A.UNIT1@NET1,87,WELL,47EE48FD-904F-4EDA-9ED9-C622D1944194,eefe228a-39a2-4742-a9e3-c07314544ada,229,Wet Well
            print("\n--- Example 4: Requesting point by IESS name ('I-0300A.UNIT1@NET1') ---")
            try:
                # Create a PointFilter object
                point_filter_iess = soapclient.factory.create('PointFilter')
                
                # Set the iessRe (IESS regular expression) filter
                # We use the exact name, but it also accepts wildcards
                point_filter_iess.iessRe = 'I-0300A.UNIT1@NET1'
                
                # Call getPoints(authstring, filter, order, startIdx, maxCount)
                # We set order, startIdx, and maxCount to None
                points_response_iess = soapclient.service.getPoints(authstring, point_filter_iess, None, None, None)
                print("Received getPoints response (by IESS):")
                print(points_response_iess)

            except Exception as e:
                print(f"Error during getPoints (by IESS): {e}")


            
            # Example 5: Get a specific point by SID
            # We will use '5395' (for I-5005A.UNIT1@NET1) from your CSV
            print("\n--- Example 5: Requesting point by SID ('5392') ---")
            try:
                # Create another PointFilter object
                point_filter_sid = soapclient.factory.create('PointFilter')
                
                # Add the SID to the 'sid' array in the filter
                # (PointFilter definition on page 19 shows sid[] = <empty>)
                point_filter_sid.sid.append(5395)
                
                # Call getPoints
                points_response_sid = soapclient.service.getPoints(authstring, point_filter_sid, None, None, None)
                print("Received getPoints response (by SID):")
                print(points_response_sid)

            except Exception as e:
                print(f"Error during getPoints (by SID): {e}")

            # -----------------------------------------------

        except Exception as e:
            from pipeline.api.eds.exceptions import connection_error_message
            EdsRestClient.connection_error_message(e, url = eds_soap_api_url)
            
        finally:
            # 4. Logout using the authstring
            if authstring and soapclient:
                print(f"\nLogging out with authstring: {authstring}...")
                try:
                    soapclient.service.logout(authstring)
                    print("Logout successful.")
                except Exception as e:
                    print(f"Error during logout: {e}")
            else:
                print("\nSkipping logout (was not logged in).")    
    
    