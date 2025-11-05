# RabbitMQ in Kubernetes - Issue Resolution

## Problem Identified

Your Kubernetes manifests were **referencing RabbitMQ but not actually deploying it**. This is why RabbitMQ couldn't work in K8s.

### What Was Missing

1. **No RabbitMQ Deployment** - Your manifests had:
   - ✅ RabbitMQ configuration (ConfigMap)
   - ✅ RabbitMQ secrets (credentials)
   - ✅ RabbitMQ consumer deployment (`connectivity-document-consumer`)
   - ✅ NodePort service to expose RabbitMQ
   - ❌ **No actual RabbitMQ pod/deployment**

2. **No Database/Cache Deployments** - Similarly missing:
   - ❌ MariaDB deployment
   - ❌ Redis deployment

Your application pods were trying to connect to services that didn't exist!

## Solution Implemented

### 1. Created RabbitMQ Deployment
**File:** `k8s/base/rabbitmq-deployment.yaml`

- Deployment with RabbitMQ 3.12 management image
- Exposed ports: 5672 (AMQP), 15672 (Management UI)
- Configured with credentials from secrets
- Health checks (startup, liveness, readiness)
- Resource limits (256Mi-512Mi memory, 200m-500m CPU)

### 2. Created Dependencies Deployment
**File:** `k8s/base/dependencies-deployment.yaml`

**MariaDB:**
- MariaDB 10.11 image
- Port 3306 exposed
- Database initialization with credentials
- Health probes

**Redis:**
- Redis 7 Alpine image
- Port 6379 exposed
- Persistence enabled (appendonly)
- Health probes

### 3. Updated Local Overlay
**File:** `k8s/overlays/local/secret-patch.yaml`

Updated secret values to point to in-cluster services:
```yaml
RABBITMQ_HOST: "rabbitmq-local"  # Service name with -local suffix
DB_HOST: "mariadb-local"
REDIS_HOST: "redis-local"
```

## Current K8s Resources

After the fix, your local overlay now deploys:

| Resource Type | Count | Names |
|--------------|-------|-------|
| **Namespace** | 1 | connectivity-local |
| **ServiceAccount** | 1 | connectivity-sa-local |
| **ConfigMap** | 1 | connectivity-config-local |
| **Secret** | 1 | connectivity-secrets-local |
| **Services** | 9 | connectivity-service, mariadb, redis, rabbitmq (ClusterIP) + 5 NodePort services |
| **Deployments** | 5 | connectivity-service, document-consumer, mariadb, redis, rabbitmq |

## Service Endpoints (NodePort)

Access your services via Minikube IP:

| Service | Internal Port | NodePort | URL Pattern |
|---------|--------------|----------|-------------|
| **Application** | 8000 | 30080 | `http://<MINIKUBE_IP>:30080` |
| **MariaDB** | 3306 | 30306 | `mysql://<MINIKUBE_IP>:30306` |
| **Redis** | 6379 | 30379 | `redis://<MINIKUBE_IP>:30379` |
| **RabbitMQ AMQP** | 5672 | 30672 | `amqp://<MINIKUBE_IP>:30672` |
| **RabbitMQ UI** | 15672 | 31672 | `http://<MINIKUBE_IP>:31672` |
| **Prometheus** | 9090 | 30090 | `http://<MINIKUBE_IP>:30090` |
| **Grafana** | 3000 | 30300 | `http://<MINIKUBE_IP>:30300` |

## Why It Works Now

### Service Discovery
In Kubernetes, pods in the same namespace can discover each other by **service name**:

- `rabbitmq-local` → resolves to RabbitMQ pod IP
- `mariadb-local` → resolves to MariaDB pod IP
- `redis-local` → resolves to Redis pod IP

### Complete Stack
Now all dependencies are deployed:
```
┌─────────────────────────────────────────┐
│         connectivity-local              │
│  (Namespace)                            │
│                                         │
│  ┌─────────────┐    ┌───────────────┐  │
│  │ Django App  │───▶│  RabbitMQ     │  │
│  │ (Web)       │    │  (Broker)     │  │
│  └─────────────┘    └───────────────┘  │
│         │                    ▲          │
│         │                    │          │
│         ▼                    │          │
│  ┌─────────────┐    ┌───────────────┐  │
│  │  MariaDB    │    │  Consumer     │  │
│  │  (DB)       │    │  (Worker)     │  │
│  └─────────────┘    └───────────────┘  │
│         │                               │
│         ▼                               │
│  ┌─────────────┐                       │
│  │   Redis     │                       │
│  │  (Cache)    │                       │
│  └─────────────┘                       │
└─────────────────────────────────────────┘
```

## How to Deploy

### Quick Validation (No Deployment)
```bash
# Validate manifests
kubectl kustomize k8s/overlays/local

# Dry run
kubectl apply --dry-run=client -k k8s/overlays/local
```

### Full Deployment
```bash
# Use the deployment script
./deploy-local-k8s.sh

# Or manually
minikube start
docker build -t connectivity-microservice:local-latest .
kubectl apply -k k8s/overlays/local

# Get Minikube IP
minikube ip

# Check deployments
kubectl get all -n connectivity-local
```

## Previous Test Experience

You mentioned testing RabbitMQ in K8s before. You likely had:
- A separate RabbitMQ deployment manifest
- Or used a Helm chart
- Or had it in a different project (like `citizen-affiliation-service`)

The issue this time was that the **application expected RabbitMQ but the manifests didn't deploy it**.

## Production Considerations

For production deployments, consider:

1. **Persistent Storage** - Replace `emptyDir` with PersistentVolumeClaims
2. **StatefulSets** - Use StatefulSets instead of Deployments for databases
3. **External Services** - Use managed services (RDS, ElastiCache, Amazon MQ)
4. **High Availability** - Run multiple replicas with proper replication
5. **Backup/Recovery** - Implement backup strategies
6. **Secrets Management** - Use sealed secrets or external secret stores
7. **Resource Limits** - Adjust based on actual load testing

## Next Steps

1. **Test Locally** - Run `./deploy-local-k8s.sh` to test full stack
2. **Access RabbitMQ UI** - `http://<MINIKUBE_IP>:31672` (admin/rabbitmq_dev_password)
3. **Check Logs** - `kubectl logs -n connectivity-local -l app=rabbitmq`
4. **Test Consumer** - Verify document consumer processes messages
5. **Update Other Overlays** - Apply same pattern to dev/staging/prod

## Validation Results

✅ All manifests validated successfully:
- 1 Namespace
- 1 ServiceAccount  
- 1 ConfigMap
- 1 Secret
- 9 Services (4 ClusterIP + 5 NodePort)
- 5 Deployments (app, consumer, mariadb, redis, rabbitmq)

The K8s setup is now complete and ready for deployment! 🚀
