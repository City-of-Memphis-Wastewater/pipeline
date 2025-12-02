## Node-RED Exec Node Configuration for Schema Generation

This section details the configuration for the Node-RED `Exec` node required to run your `scripts/generate_schema.py` file. This node will be placed directly after the "Config Key Registry" function node in your "Multi-Client Configuration Flow."

### 1. Contents of the Exec Node

The `Exec` node is designed to run shell commands.

|   |   |   |
|---|---|---|
|**Property**|**Value**|**Notes**|
|**Name**|Run Python Schema Generator|A clear name for the node.|
|**Command**|`python scripts/generate_schema.py`|This executes the Python script.|
|**Append `msg.payload`**|`unchecked`|We don't want to pass the message payload as arguments to the script.|
|**Wait for command to complete?**|`checked`|Yes, we need the script to finish before proceeding.|
|**Working Directory**|`/home/oolong/dev/pipeline`|**CRITICAL:** This must be set to your project root to ensure `from pipeline.config.key_registry import...` works correctly. Adjust this path to your exact project root location (`~/dev/pipeline`).|
|**Output**|`return code`|We only need the status code (0 for success).|

### 2. Adding the Node via the Node-RED Web GUI

1. **Open the Flow:** Navigate to your "Multi-Client Configuration Flow (CLI vs SPA)" tab in the Node-RED editor.
    
2. **Add Exec Node:** Drag an **Exec** node (found under the 'Advanced' section) onto the canvas.
    
3. **Configure Exec Node:** Double-click the new `Exec` node and enter the properties as listed in Section 1, paying close attention to setting the **Working Directory** to your project root.
    
4. **Wire the Flow:**
    
    - Disconnect the wire currently connecting the **"Config Key Registry (The Schema)"** function node to the two comment nodes.
        
    - Wire the output of **"Config Key Registry (The Schema)"** (the original function node that defines `msg.schema`) to the input of your new **"Run Python Schema Generator"** (the Exec node).
        
    - Wire the **second output** of the **"Run Python Schema Generator"** (labeled 'stdout') to a new **Debug node**. Name the Debug node: `SUCCESS: Schema Artifact Generated`.
        
5. **Deploy:** Click the **Deploy** button. Now, when you inject a message into the registry flow, the Python script will run, generating your `config_schema.json` file.
    

### 3. Adding the Node by Directly Editing the Flow File

If you want to add the Node-RED components by editing the flow file (`./node-red/json-schema/flow.json`), you can insert the following JSON objects. These objects correspond to the `Exec` node and a subsequent `Debug` node, and update the wiring of the "Config Key Registry" node (`6b490d1f.a46f2c`).

**A. New Nodes to Insert (Exec and Debug):**

```
    {
        "id": "7f8a9b0c.d1e2f3",
        "type": "exec",
        "z": "e67e35b0.f3c1d4",
        "name": "Run Python Schema Generator",
        "command": "python scripts/generate_schema.py",
        "addpay": false,
        "append": "",
        "useSpawn": "false",
        "timer": "",
        "oldstyle": false,
        "x": 680,
        "y": 100,
        "wires": [
            [],
            [
                "8g9h0i1j.k2l3m4"
            ],
            []
        ],
        "workingDir": "/home/oolong/dev/pipeline"
    },
    {
        "id": "8g9h0i1j.k2l3m4",
        "type": "debug",
        "z": "e67e35b0.f3c1d4",
        "name": "SUCCESS: Schema Artifact Generated",
        "active": true,
        "tosidebar": true,
        "console": false,
        "tostatus": false,
        "complete": "payload",
        "targetType": "msg",
        "statusVal": "",
        "statusType": "auto",
        "x": 1000,
        "y": 100,
        "wires": []
    }
```

**B. Update the Existing "Config Key Registry" Node:**

You must update the `wires` array of the "Config Key Registry" node (`"id": "6b490d1f.a46f2c"`) to point its output to the new Exec node (`7f8a9b0c.d1e2f3`) instead of the two comment nodes.

The old `wires` array was:

```
"wires": [["67f912e5.a4c3f2", "89b0c1d2.e3f4a5"]]
```

The **new `wires` array** should be:

```
"wires": [["7f8a9b0c.d1e2f3"]]
```

_(Note: You'll also need to re-wire the Exec node's output back to the original comment nodes if you want the signal to continue down the CLI/SPA paths, but for simplicity, the primary connection is shown above.)_