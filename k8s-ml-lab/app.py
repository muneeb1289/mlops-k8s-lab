from flask import Flask, request, jsonify
import os
import math
import time

app = Flask(__name__)

# Load configuration from environment variables (to be provided by K8s)
MODEL_NAME = os.getenv("MODEL_NAME", "base-model")
API_KEY = os.getenv("API_KEY", "default-key")

@app.route('/predict', methods=['GET'])
def predict():
    # 1. Security Check (Demonstrates Secrets)
    user_key = request.args.get('api_key')
    if user_key != API_KEY:
        return jsonify({"error": "Unauthorized"}), 401

    # 2. Simulate Heavy ML Inference (Demonstrates HPA)
    # This loop forces the CPU to work, triggering auto-scaling later.
    start_time = time.time()
    [math.sqrt(i) for i in range(5000000)] 
    latency = time.time() - start_time

    return jsonify({
        "model": MODEL_NAME,
        "prediction": "Iris-Setosa",
        "cpu_time_seconds": round(latency, 4),
        "status": "success"
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
