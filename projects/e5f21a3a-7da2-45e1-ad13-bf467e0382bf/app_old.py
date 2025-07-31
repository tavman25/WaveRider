from flask import Flask, request, jsonify
import subprocess
import json

app = Flask(__name__)

@app.route('/snmpget', methods=['POST'])
def snmp_get():
    data = request.json
    mib = data.get('mib')
    oid = data.get('oid')
    ip = data.get('ip')

    if not mib or not oid or not ip:
        return jsonify({'error': 'MIB, OID, and IP are required.'}), 400

    try:
        # Call snmpget command
        command = ['snmpget', '-v2c', '-c', 'public', ip, oid]
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        return jsonify({'result': result.stdout.strip()})
    except subprocess.CalledProcessError as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)