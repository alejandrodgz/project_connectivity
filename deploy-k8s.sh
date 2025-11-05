#!/bin/bash
set -e

echo "🚀 Deploying Connectivity Microservice to Kubernetes..."
echo ""

# Make sure minikube is running
if ! minikube status > /dev/null 2>&1; then
    echo "❌ Minikube is not running. Starting it..."
    minikube start --cpus=2 --memory=4096
fi

# Build image in minikube's docker
echo "📦 Building Docker image in Minikube..."
eval $(minikube docker-env)
docker build -t connectivity-microservice:local-latest . --quiet

# Apply Kubernetes manifests
echo "☸️  Applying Kubernetes manifests..."
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/mariadb.yaml
kubectl apply -f k8s/redis.yaml
kubectl apply -f k8s/rabbitmq.yaml

echo "⏳ Waiting for dependencies to be ready..."
kubectl wait --for=condition=ready pod -l app=mariadb -n connectivity --timeout=60s || true
kubectl wait --for=condition=ready pod -l app=redis -n connectivity --timeout=60s || true
kubectl wait --for=condition=ready pod -l app=rabbitmq -n connectivity --timeout=60s || true

echo "🚀 Deploying application..."
kubectl apply -f k8s/app.yaml
kubectl apply -f k8s/consumer.yaml

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📊 Access your services:"
MINIKUBE_IP=$(minikube ip)
echo "  - Django App: http://${MINIKUBE_IP}:30800"
echo "  - RabbitMQ UI: http://${MINIKUBE_IP}:30672 (admin/admin)"
echo "  - MariaDB: ${MINIKUBE_IP}:30306"
echo ""
echo "📝 Useful commands:"
echo "  - Check pods: kubectl get pods -n connectivity"
echo "  - View logs: kubectl logs -f deployment/connectivity-app -n connectivity"
echo "  - Delete all: kubectl delete namespace connectivity"
