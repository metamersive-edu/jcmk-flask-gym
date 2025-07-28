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
def receive_data():
    try:
        data = request.get_json(force=True)
        if not data:
            return jsonify({"error": "Empty payload"}), 400

        # Normalize to list
        entries = [data] if isinstance(data, dict) else data if isinstance(data, list) else None
        if entries is None:
            return jsonify({"error": "Invalid JSON format"}), 400

        valid_entries = []
        for entry in entries:
            try:
                valid_entries.append({
                    "cycle": int(entry["cycle"]),
                    "voltage": float(entry["voltage"]),
                    "current": abs(float(entry["current"])),
                    "power": float(entry["power"])
                })
            except Exception as e:
                print(f"[ESP] Skipped invalid entry: {entry} — {e}")

        if valid_entries:
            log_data(valid_entries)
            print(f"[ESP] Logged {len(valid_entries)} entries")
            return jsonify({"status": "ok", "count": len(valid_entries)}), 200
        else:
            return jsonify({"error": "No valid entries"}), 400

    except Exception as e:
        print(f"[ESP] Error: {e}")
        return jsonify({"error": str(e)}), 500
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)
