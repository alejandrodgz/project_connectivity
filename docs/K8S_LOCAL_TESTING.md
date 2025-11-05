# 🧪 Local Kubernetes Testing Guide

## 🚀 Quick Start

```bash
# One command to deploy everything
./deploy-local-k8s.sh
```

This will:
1. ✅ Start Minikube (if not running)
2. ✅ Build Docker image inside Minikube
3. ✅ Deploy all services to Kubernetes
4. ✅ Show you all access URLs

## 🌐 Access URLs (after deployment)

Once deployed, you'll get URLs like this (replace `<MINIKUBE_IP>` with your actual IP):

| Service | URL | Port |
|---------|-----|------|
| **Django App** | `http://<MINIKUBE_IP>:30080` | 30080 |
| **Health Check** | `http://<MINIKUBE_IP>:30080/health/live` | 30080 |
| **Metrics** | `http://<MINIKUBE_IP>:30080/metrics` | 30080 |
| **API Docs** | `http://<MINIKUBE_IP>:30080/api/schema/swagger-ui/` | 30080 |
| **MariaDB** | `<MINIKUBE_IP>:30306` | 30306 |
| **Redis** | `<MINIKUBE_IP>:30379` | 30379 |
| **RabbitMQ AMQP** | `<MINIKUBE_IP>:30672` | 30672 |
| **RabbitMQ UI** | `http://<MINIKUBE_IP>:31672` | 31672 |
| **Prometheus** | `http://<MINIKUBE_IP>:30090` | 30090 |
| **Grafana** | `http://<MINIKUBE_IP>:30300` | 30300 |

## 📋 Manual Steps (if you prefer)

### 1. Start Minikube
```bash
minikube start --cpus=4 --memory=8192
```

### 2. Build Image in Minikube
```bash
# Use Minikube's Docker daemon
eval $(minikube docker-env)

# Build image
docker build -t connectivity-microservice:local-latest .
```

### 3. Deploy to Kubernetes
```bash
kubectl apply -k k8s/overlays/local
```

### 4. Check Status
```bash
kubectl get all -n connectivity-local
```

### 5. Get Minikube IP
```bash
minikube ip
```

## 🔍 Useful Commands

### View All Resources
```bash
kubectl get all -n connectivity-local
```

### View Logs
```bash
# Web service
kubectl logs -f deployment/connectivity-service-local -n connectivity-local

# Document consumer
kubectl logs -f deployment/connectivity-document-consumer-local -n connectivity-local

# All pods
kubectl logs -f -l app=connectivity-service -n connectivity-local --all-containers=true
```

### Port Forward (Alternative to NodePort)
```bash
# Django app
kubectl port-forward -n connectivity-local svc/connectivity-service-local 8000:80

# RabbitMQ Management
kubectl port-forward -n connectivity-local svc/rabbitmq-nodeport 15672:15672

# Prometheus
kubectl port-forward -n connectivity-local svc/prometheus-nodeport 9090:9090

# Grafana
kubectl port-forward -n connectivity-local svc/grafana-nodeport 3000:3000
```

### Scale Deployments
```bash
kubectl scale deployment/connectivity-service-local --replicas=3 -n connectivity-local
```

### Restart Deployments
```bash
kubectl rollout restart deployment/connectivity-service-local -n connectivity-local
```

### Delete Everything
```bash
kubectl delete -k k8s/overlays/local
```

## 🧪 Test the Application

### 1. Check Health
```bash
MINIKUBE_IP=$(minikube ip)
curl http://${MINIKUBE_IP}:30080/health/live
curl http://${MINIKUBE_IP}:30080/health/ready
```

### 2. Get JWT Token
```bash
# You'll need to create a service account first inside the pod
kubectl exec -it deployment/connectivity-service-local -n connectivity-local -- python manage.py create_service_account test_service
```

### 3. Test Affiliation Check
```bash
# Get token and test
curl -X POST http://${MINIKUBE_IP}:30080/api/v1/affiliation/check/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"citizen_id": "1128456232"}'
```

### 4. Access RabbitMQ UI
Open browser: `http://<MINIKUBE_IP>:31672`
- Username: `admin`
- Password: `admin`

### 5. Access Grafana
Open browser: `http://<MINIKUBE_IP>:30300`
- Username: `admin`
- Password: `admin`

## 🔧 Troubleshooting

### Pods not starting?
```bash
# Describe pod to see events
kubectl describe pod <pod-name> -n connectivity-local

# Check events
kubectl get events -n connectivity-local --sort-by='.lastTimestamp'
```

### Database connection issues?
```bash
# Check if DB is ready
kubectl get pods -n connectivity-local | grep mariadb

# Test connection from pod
kubectl exec -it deployment/connectivity-service-local -n connectivity-local -- python manage.py dbshell
```

### Image not found?
```bash
# Make sure you're using Minikube's Docker
eval $(minikube docker-env)

# Rebuild
docker build -t connectivity-microservice:local-latest .

# Verify image exists
docker images | grep connectivity
```

## 🧹 Cleanup

### Stop everything but keep Minikube
```bash
kubectl delete -k k8s/overlays/local
```

### Stop Minikube
```bash
minikube stop
```

### Delete Minikube completely
```bash
minikube delete
```

## 📊 Monitoring

### View Metrics
```bash
MINIKUBE_IP=$(minikube ip)
curl http://${MINIKUBE_IP}:30080/metrics
```

### Prometheus Targets
Visit: `http://<MINIKUBE_IP>:30090/targets`

### Resource Usage
```bash
kubectl top pods -n connectivity-local
kubectl top nodes
```

---

**Tip:** Save the Minikube IP to avoid typing it every time:
```bash
export MINIKUBE_IP=$(minikube ip)
echo "Minikube IP: $MINIKUBE_IP"
```
