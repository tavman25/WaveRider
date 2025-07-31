# SNMPGet Microservice

## Description
This microservice utilizes Python to intake a MIB and an IP/FQDN and uses `snmpget` to query using that data to provide a return to be ingested by another service.

## Features
- Basic functionality to query SNMP data.

## Requirements
- Python 3.7+
- pip
- snmpget (part of net-snmp package)

## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/snmpget-microservice.git
   cd snmpget-microservice
   ```
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```
3. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the service:
   ```bash
   python app.py
   ```

## Usage
Send a POST request to `/snmpget` with JSON body:
```json
{
  "mib": "IF-MIB",
  "oid": "1.3.6.1.2.1.2.2.1.2.2",
  "ip": "192.168.1.1"
}
```

## License
This project is licensed under the MIT License.