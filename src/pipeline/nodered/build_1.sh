#!/bin/bash
mkdir -p flows/api
cat << EOF > flows/api/rjn_login.json
[{"id":"login_subflow","type":"subflow","name":"RJN Login","info":"","category":"","in":[...]}]  # Paste login part JSON here
EOF
cat << EOF > flows/api/rjn_send.json
[{"id":"send_subflow","type":"subflow","name":"RJN Send Data","info":"","category":"","in":[...]}]  # Paste send part
EOF
cat << EOF > flows/api/rjn_ping.json
[{"id":"ping_subflow","type":"subflow","name":"RJN Ping","info":"","category":"","in":[...]}]  # Paste ping part
EOF
echo "Created flows/api/ with subflows. Import each JSON into Node-RED."
