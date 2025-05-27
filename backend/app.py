from flask import Flask, jsonify, request
import platform
import datetime

app = Flask(__name__)

@app.route('/', methods=['GET'])
def status():
    tls_info = {
        "version": request.headers.get("X-TLS-Version", "unbekannt"),
        "cipher": request.headers.get("X-TLS-Cipher", "unbekannt"),
        "post_quantum_enabled": True  # Setzt du manuell nach deiner Konfiguration
    }

    response = {
        "server_time": datetime.datetime.utcnow().isoformat() + "Z",
        "server_info": {
            "os": platform.system(),
            "os_version": platform.version(),
            "hostname": platform.node()
        },
        "tls": tls_info,
        "status": "online"
    }

    return jsonify(response)

if __name__ == '__main__':
    # Server auf Port 5000 starten, ohne Debug im produktiven Einsatz bitte deaktivieren
    app.run(host='0.0.0.0', port=5000)