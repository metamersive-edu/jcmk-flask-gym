from flask import Flask
from flask import request, jsonify
from ui import ui_blueprint
from register_api import register_api
from leaderboard_api import leaderboard_json
from energy_api import energy_api
from tracker import log_data
from wifi_listener import WifiPoller
import threading
from competition_api import competition_api
import os
app = Flask(__name__)

# Register all blueprints
app.register_blueprint(ui_blueprint)
app.register_blueprint(register_api)
app.register_blueprint(leaderboard_json)
app.register_blueprint(energy_api)
app.register_blueprint(competition_api)
# Define the function that WifiPoller will call on receiving data
@app.route("/api/receive_data", methods=["POST"])
def handle_data():
    data = request.get_json(force=True)
    print("[DEBUG] Raw incoming data:", data)

    if not isinstance(data, dict) or "channels" not in data:
        print("[ERROR] Invalid format: no 'channels' key")
        return jsonify({"error": "No valid entries"}), 400

    entries = data["channels"]
    valid_entries = []

    for entry in entries:
        print(f"[DEBUG] Entry: {entry}")
        if entry.get("connected") != 1:
            print("[DEBUG] Skipping entry: not connected")
            continue

        try:
            # Discard if voltage > 14V (14,000 mV)
            if entry["voltage_mV"] > 14000:
                print(f"[WARN] Discarding entry for channel {entry['channel']} - Voltage too high ({entry['voltage_mV']} mV)")
                continue

            cleaned = {
                "cycle": entry["channel"] + 1,
                "voltage": entry["voltage_mV"] / 1000,
                "current": abs(entry["current_mA"] / 1000),
                "power": entry["power_mW"] / 1000,
            }
            valid_entries.append(cleaned)
        except Exception as e:
            print(f"[ERROR] Conversion failed: {e}")

    if valid_entries:
        log_data(valid_entries)
        print(f"[SUCCESS] Logged {len(valid_entries)} entries.")
        return jsonify({"status": "success", "count": len(valid_entries)}), 200
    else:
        print("[WARN] No valid entries found.")
        return jsonify({"error": "No valid entries"}), 400

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)
