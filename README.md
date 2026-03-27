[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/kxkTj_1S)
# mlops-spring-2026-kubenetes-introduction
To bridge the gap between pure coding and Kubernetes orchestration, this lab is divided into two phases: **The Application Build** and **The Kubernetes Deployment**. 

In the first phase, students act as **ML Engineers** building the service. In the second, they act as **DevOps Engineers** deploying it to a production-like environment.

---

## Phase 1: Developing the ML Application

Students will create a Python-based Flask API. This application simulates a CPU-intensive "prediction" task to ensure the Kubernetes Horizontal Pod Autoscaler (HPA) has something to react to.

### 1. The Python Script (`app.py`)
Have students create a folder named `k8s-ml-lab` and save this code:

```python
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
```

### 2. Containerization (`Dockerfile`)
Students must package the app. Explain that the `Dockerfile` ensures the app runs the same on their laptop as it does in the cluster.

```dockerfile
FROM python:3.9-slim
WORKDIR /app
RUN pip install flask
COPY app.py .
EXPOSE 5000
CMD ["python", "app.py"]
```

---

## Phase 2: The Kubernetes Lab (Minikube)

Now, students will move this image into the Minikube environment.

### 1. Build the Image inside Minikube
Instead of pushing to DockerHub, we build directly into Minikube’s internal registry:
```bash
# Point your terminal to minikube's docker daemon
eval $(minikube docker-env)

# Build the image
docker build -t ml-predictor:v1 .
```

### 2. Define the Infrastructure (`manifest.yaml`)
Students should create one file (or separate ones) containing the **Secret**, **ConfigMap**, **Deployment**, and **Service**.

```yaml
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: ml-config
data:
  MODEL_NAME: "v1-production-iris"
---
apiVersion: v1
kind: Secret
metadata:
  name: ml-auth
type: Opaque
stringData:
  API_KEY: "secret-token-2024"
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ml-deployment
spec:
  replicas: 1
  selector:
    matchLabels:
      app: ml-api
  template:
    metadata:
      labels:
        app: ml-api
    spec:
      containers:
      - name: ml-container
        image: ml-predictor:v1
        imagePullPolicy: Never
        resources:
          requests:
            cpu: "100m"
          limits:
            cpu: "200m"
        env:
        - name: MODEL_NAME
          valueFrom:
            configMapKeyRef:
              name: ml-config
              key: MODEL_NAME
        - name: API_KEY
          valueFrom:
            secretKeyRef:
              name: ml-auth
              key: API_KEY
---
apiVersion: v1
kind: Service
metadata:
  name: ml-service
spec:
  type: NodePort
  selector:
    app: ml-api
  ports:
    - port: 80
      targetPort: 5000
```

---

## Phase 3: Scaling Exercise (Generating Load)

Students need to see Kubernetes "breathe" by adding more pods automatically.

1.  **Enable the Metrics Server:** `minikube addons enable metrics-server`
2.  **Define the HPA:** `kubectl autoscale deployment ml-deployment --cpu-percent=30 --min=1 --max=5`
3.  **The Attack (Load Generation):**
    Students open a new terminal and run a "stress test" loop:
    ```bash
    SERVICE_URL=$(minikube service ml-service --url)
    while true; do curl "$SERVICE_URL/predict?api_key=secret-token-2024"; done
    ```
4.  **Observation:**
    In another terminal, watch the pods multiply:
    `kubectl get pods -w`

---

## Lab Exercise Questions

1.  **The Environment Trap:** If you change the `MODEL_NAME` in the `ConfigMap` while the app is running, does the output of the `/predict` endpoint change immediately? Why or why not?
2.  **Security Audit:** Describe the command to view the value of the `API_KEY` stored in the Secret. Is it truly encrypted or just encoded? (Hint: Check `base64 --decode`).
3.  **Scaling Logic:** Based on your load test, how long did it take for the HPA to trigger the second pod? Research the "Stabilization Window" in Kubernetes HPA documentation.
4.  **Fault Tolerance:** Delete the running pod using `kubectl delete pod [pod-name]`. What does Kubernetes do immediately after? How does this relate to the "Desired State" concept?
5.  **ML Implementation:** Modify the `app.py` to include a second route `/health` that returns a 200 OK status. Update the Kubernetes `manifest.yaml` to include a `livenessProbe` using this new route.
