#!/bin/bash
# Script to create the Node-RED flow demonstrating Code to Diagram Generation

FLOW_FILE="./node-red/code-diagram/flow.json"
mkdir -p $(dirname $FLOW_FILE)

echo "Creating Node-RED flow for Code Diagramming in $FLOW_FILE"

cat > $FLOW_FILE << 'EOF'
[
    {
        "id": "270f2f3e.34d4d6",
        "type": "tab",
        "label": "Generic Code-to-Diagram Flow",
        "disabled": false,
        "info": "Demonstrates the stages of converting source code into an architectural diagram using a Diagram-as-Code approach (like Mermaid or PlantUML)."
    },
    {
        "id": "6b3a0b2c.a1b3c4",
        "type": "inject",
        "z": "270f2f3e.34d4d6",
        "name": "Input Source Code",
        "props": [
            {
                "p": "payload",
                "v": "class EdsSoapClient:\n    def get_data():\n        config = SecurityAndConfig()\n        url = config.get_url(KEY_A)\n        auth = config.get_credentials(KEY_B)\n        # ... API call ...",
                "vt": "str"
            }
        ],
        "repeat": "",
        "crontab": "",
        "once": true,
        "onceDelay": 0.1,
        "topic": "",
        "x": 140,
        "y": 140,
        "wires": [
            [
                "7d8c4e5f.b6a7d8"
            ]
        ]
    },
    {
        "id": "7d8c4e5f.b6a7d8",
        "type": "function",
        "z": "270f2f3e.34d4d6",
        "name": "1. Code Scanner / Parser",
        "func": "/*\n  Simulates a tool (e.g., AST parser) scanning the code to identify \n  classes, relationships (composition, dependency), and interfaces.\n*/\n\nconst code = msg.payload;\nconst relationships = [\n    { source: \"EdsSoapClient\", target: \"SecurityAndConfig\", type: \"Dependency\" },\n    { source: \"SecurityAndConfig\", target: \"Config.json\", type: \"Read/Write\" },\n    { source: \"SecurityAndConfig\", target: \"Keyring\", type: \"Read\" }\n];\n\nmsg.relationships = relationships;\nmsg.payload = \"Relationships Extracted\";\nreturn msg;",
        "outputs": 1,
        "noerr": 0,
        "initialize": "",
        "finalize": "",
        "libs": [],
        "x": 420,
        "y": 140,
        "wires": [
            [
                "8e9f0a1b.c2d3e4"
            ]
        ]
    },
    {
        "id": "8e9f0a1b.c2d3e4",
        "type": "function",
        "z": "270f2f3e.34d4d6",
        "name": "2. Diagram DSL Generator (Mermaid)",
        "func": "/*\n  Converts the structured relationships into a Diagram-as-Code language,\n  such as Mermaid (for UML or Sequence diagrams).\n*/\n\nlet mermaidDSL = \"graph TD\\n\";\nmermaidDSL += \"A[EdsSoapClient] --> B(SecurityAndConfig)\\n\";\nmermaidDSL += \"B --> C[Config.json]\\n\";\nmermaidDSL += \"B --> D[Keyring]\\n\";\nmermaidDSL += \"D -- Creds --> E((User/OS Store))\\n\";\nmermaidDSL += \"A -- Calls -- B\\n\";\nmermaidDSL += \"subgraph Persistence\\n    C\\n    D\\n    E\\nend\\n\";\n\nmsg.mermaid_dsl = mermaidDSL;\nmsg.payload = mermaidDSL;\nreturn msg;",
        "outputs": 1,
        "noerr": 0,
        "initialize": "",
        "finalize": "",
        "libs": [],
        "x": 680,
        "y": 140,
        "wires": [
            [
                "9f0b2c3d.d4e5f6",
                "a1b2c3d4.e5f6a7"
            ]
        ]
    },
    {
        "id": "9f0b2c3d.d4e5f6",
        "type": "debug",
        "z": "270f2f3e.34d4d6",
        "name": "DEBUG: Generated Mermaid DSL",
        "active": true,
        "tosidebar": true,
        "console": false,
        "tostatus": false,
        "complete": "payload",
        "targetType": "msg",
        "statusVal": "",
        "statusType": "auto",
        "x": 700,
        "y": 80,
        "wires": []
    },
    {
        "id": "a1b2c3d4.e5f6a7",
        "type": "comment",
        "z": "270f2f3e.34d4d6",
        "name": "3. External Diagram Service (Simulated)",
        "info": "In a real environment, you would send the Mermaid DSL to a rendering service (like an official Mermaid API or a self-hosted PlantUML server) to generate a PNG or SVG image.",
        "x": 980,
        "y": 140,
        "wires": []
    }
]
EOF

echo "Flow saved to $FLOW_FILE"
echo "To import, open Node-RED, go to Import -> Flows, and paste the content of $FLOW_FILE."