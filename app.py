from flask import Flask, request, jsonify
from flask_cors import CORS
from hmpi_calculator import calculate_indices
import pandas as pd
from io import StringIO

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests from your frontend

# Helper to validate numeric fields
def validate_metal_value(value, name):
    try:
        val = float(value)
        if val < 0:
            raise ValueError(f"{name} cannot be negative.")
        return val
    except Exception:
        raise ValueError(f"{name} must be a numeric value.")

# Manual calculation endpoint
@app.route("/api/hmpi/calculate", methods=["POST"])
def calculate_hmpi_manual():
    data = request.get_json()
    if not data or "heavyMetalConcentrations" not in data:
        return jsonify({"error": "Missing heavyMetalConcentrations in request body"}), 400

    try:
        metals = data["heavyMetalConcentrations"]
        # Validate and convert all values to float
        metals_clean = {k: validate_metal_value(v, k) for k, v in metals.items()}
        indices = calculate_indices(metals_clean)
        return jsonify(indices), 200
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        return jsonify({"error": "Internal server error"}), 500

# Batch CSV calculation endpoint
@app.route("/api/hmpi/calculate-batch", methods=["POST"])
def calculate_hmpi_batch():
    data = request.get_json()
    if not data or "records" not in data:
        return jsonify({"error": "Missing records in request body"}), 400

    results = []
    for row in data["records"]:
        try:
            metals = {k: validate_metal_value(row[k], k) for k in row if k not in ["sampleNo", "state", "location", "latitude", "longitude"] and row[k] is not None}
            indices = calculate_indices(metals)
            result = {**row, **indices}  # Merge original row with calculated indices
            results.append(result)
        except ValueError as ve:
            results.append({**row, "error": str(ve)})
        except Exception:
            results.append({**row, "error": "Calculation failed"})

    return jsonify({"results": results}), 200


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8000)
