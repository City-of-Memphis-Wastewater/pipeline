#!/bin/bash
# Script to create the Node-RED flow demonstrating Configuration-as-Code Schema Generation

FLOW_FILE="./node-red/json-schema/flow.json"
mkdir -p $(dirname $FLOW_FILE)

echo "Creating Node-RED flow for JSON Schema Generation in $FLOW_FILE"

cat > $FLOW_FILE << 'EOF'
[
    {
        "id": "e67e35b0.f3c1d4",
        "type": "tab",
        "label": "Config-as-Code Flow (Schema Generation)",
        "disabled": false,
        "info": "Simulates the process where a Python Key Registry generates a stable JSON Schema for client consumption."
    },
    {
        "id": "119e71d2.65345a",
        "type": "inject",
        "z": "e67e35b0.f3c1d4",
        "name": "Trigger Schema Build",
        "props": [
            {
                "p": "payload"
            }
        ],
        "repeat": "",
        "crontab": "",
        "once": true,
        "onceDelay": 0.1,
        "topic": "",
        "payload": "start",
        "payloadType": "str",
        "x": 140,
        "y": 140,
        "wires": [
            [
                "6b490d1f.a46f2c"
            ]
        ]
    },
    {
        "id": "6b490d1f.a46f2c",
        "type": "function",
        "z": "e67e35b0.f3c1d4",
        "name": "1. Python Key Registry (Source of Truth)",
        "func": "/*\n  Simulated contents of src/pipeline/config/key_registry.py\n  This defines the schema, prompt, and storage requirements.\n*/\n\nmsg.registry = [\n    {\n        \"key_stem\": \"eds_base_url\",\n        \"type\": \"string\",\n        \"security_level\": \"PLAINTEXT\",\n        \"prompt_message\": \"Enter the EDS base URL (e.g., http://0.0.0.0)\",\n        \"plant_dependent\": true\n    },\n    {\n        \"key_stem\": \"username\",\n        \"type\": \"string\",\n        \"security_level\": \"CREDENTIAL\",\n        \"prompt_message\": \"Enter your API username\",\n        \"plant_dependent\": false\n    },\n    {\n        \"key_stem\": \"timeout_seconds\",\n        \"type\": \"integer\",\n        \"security_level\": \"PLAINTEXT\",\n        \"prompt_message\": \"Enter the default API timeout in seconds\",\n        \"default_value\": 30\n    }\n];\n\nmsg.payload = \"Key Registry Loaded\";\nreturn msg;",
        "outputs": 1,
        "noerr": 0,
        "initialize": "",
        "finalize": "",
        "libs": [],
        "x": 420,
        "y": 140,
        "wires": [
            [
                "15b5302f.e8f731"
            ]
        ]
    },
    {
        "id": "15b5302f.e8f731",
        "type": "function",
        "z": "e67e35b0.f3c1d4",
        "name": "2. Schema Generator (Build Script)",
        "func": "/*\n  Simulates a build script that iterates over the Python registry \n  and translates it into a standard JSON Schema artifact.\n*/\n\nconst schema = {\n    \"$schema\": \"http://json-schema.org/draft-07/schema#\",\n    \"title\": \"EDS Configuration Schema\",\n    \"type\": \"object\",\n    \"properties\": {}\n};\n\nmsg.registry.forEach(item => {\n    schema.properties[item.key_stem] = {\n        \"type\": item.type,\n        \"description\": item.prompt_message,\n        \"default\": item.default_value\n    };\n});\n\nmsg.schema = schema;\nmsg.payload = schema;\nreturn msg;",
        "outputs": 1,
        "noerr": 0,
        "initialize": "",
        "finalize": "",
        "libs": [],
        "x": 680,
        "y": 140,
        "wires": [
            [
                "37f71e51.f82b82",
                "0f0e2195.f938d2"
            ]
        ]
    },
    {
        "id": "37f71e51.f82b82",
        "type": "debug",
        "z": "e67e35b0.f3c1d4",
        "name": "DEBUG: Generated JSON Schema (Artifact)",
        "active": true,
        "tosidebar": true,
        "console": false,
        "tostatus": false,
        "complete": "payload",
        "targetType": "msg",
        "statusVal": "",
        "statusType": "auto",
        "x": 730,
        "y": 80,
        "wires": []
    },
    {
        "id": "0f0e2195.f938d2",
        "type": "function",
        "z": "e67e35b0.f3c1d4",
        "name": "3. Client Consumption (Svelte/Web UI)",
        "func": "/*\n  Simulates a Svelte/Web UI reading the stable JSON Schema \n  to dynamically generate a configuration form (labels, inputs, etc.)\n*/\n\nconst properties = msg.schema.properties;\nlet htmlForm = \"<form>\\n\";\n\nfor (const key in properties) {\n    if (properties.hasOwnProperty(key)) {\n        const prop = properties[key];\n        htmlForm += `  <label for='${key}'>${prop.description}</label>\\n`;\n        let type = 'text';\n        if (prop.type === 'integer') { type = 'number'; }\n        \n        htmlForm += `  <input type='${type}' id='${key}' name='${key}' placeholder='${prop.default !== undefined ? prop.default : ''}'><br>\\n`;\n    }\n}\n\nhtmlForm += \"</form>\";\n\nmsg.payload = htmlForm;\nreturn msg;",
        "outputs": 1,
        "noerr": 0,
        "initialize": "",
        "finalize": "",
        "libs": [],
        "x": 930,
        "y": 140,
        "wires": [
            [
                "617d3635.c0903a"
            ]
        ]
    },
    {
        "id": "617d3635.c0903a",
        "type": "debug",
        "z": "e67e35b0.f3c1d4",
        "name": "DEBUG: Svelte/Web Form Output",
        "active": true,
        "tosidebar": true,
        "console": false,
        "tostatus": false,
        "complete": "payload",
        "targetType": "msg",
        "statusVal": "",
        "statusType": "auto",
        "x": 1150,
        "y": 140,
        "wires": []
    }
]
EOF

echo "Flow saved to $FLOW_FILE"
echo "To import, open Node-RED, go to Import -> Flows, and paste the content of $FLOW_FILE."
