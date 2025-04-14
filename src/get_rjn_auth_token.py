#src.get_rjn_auth_token.py

import os
import sys
import subprocess


# Add the project directory to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

#sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
#sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from env.env_ import Env
except:
    from ..env.env_ import Env

def call_curl_script(username =  Env.get_username(),password =  Env.get_password()):
    curl_statement = f"""
    curl --location 'https://rjn-clarity-api.com/v1/clarity/auth' \
    --header 'Content-Type: application/json' \
    --data '{{"client_id": "{username}","password": "{password}"}}'
    """
    # Capture the response from the curl command
    result = subprocess.run(curl_statement, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    print(result)

def stff(result):
    if result.returncode == 0:
        # Parse the output assuming it's JSON
        try:
            response_json = json.loads(result.stdout)
            auth_token = response_json.get("auth_token", None)

            if auth_token:
                # Save the auth token to a file
                with open(output_file, 'w') as file:
                    file.write(auth_token)
                print(f"Auth token saved to {output_file}")
            else:
                print("Error: Auth token not found in response.")
        except json.JSONDecodeError:
            print("Error: Failed to parse JSON from response.")
    else:
        print(f"Error: Curl command failed with return code {result.returncode}.")
        print(f"stderr: {result.stderr}")
if __name__ == "__main__":
    call_curl_script(username =  Env.get_username(),password =  Env.get_password())



    