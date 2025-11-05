# 🚀 Quick Reference - CI/CD & Kubernetes

## 📝 Daily Commands

### Local Development
```bash
# Run tests
pytest apps/ infrastructure/ --cov=apps --cov=infrastructure -v

# Check code quality
black --check apps/ infrastructure/ settings/
flake8 apps/ infrastructure/ settings/
isort --check-only apps/ infrastructure/ settings/

# Auto-fix formatting
black apps/ infrastructure/ settings/
isort apps/ infrastructure/ settings/

# Run security scan
bandit -r apps/ infrastructure/
```

### Docker
```bash
# Build image
docker build -t connectivity-microservice:local .

# Run locally
docker-compose up

# View logs
docker-compose logs -f web
docker-compose logs -f document-consumer
```

### Kubernetes - Development
```bash
# Deploy
kubectl apply -k k8s/overlays/development

# Check status
kubectl get all -n connectivity-dev

# View logs
kubectl logs -f deployment/connectivity-service-dev -n connectivity-dev

# Port forward
kubectl port-forward svc/connectivity-service-dev -n connectivity-dev 8000:80

# Delete
kubectl delete -k k8s/overlays/development
```

### Kubernetes - Production
```bash
# Deploy
kubectl apply -k k8s/overlays/production

# Check status
kubectl get all -n connectivity
kubectl rollout status deployment/connectivity-service -n connectivity

# View logs
kubectl logs -f deployment/connectivity-service -n connectivity

# Scale
kubectl scale deployment/connectivity-service --replicas=5 -n connectivity

# Rollback
kubectl rollout undo deployment/connectivity-service -n connectivity
```

## 🔍 Troubleshooting

### Pod Not Starting
```bash
# Describe pod
kubectl describe pod <pod-name> -n connectivity

# Get events
kubectl get events -n connectivity --sort-by='.lastTimestamp'

# Check logs
kubectl logs <pod-name> -n connectivity
```

### Database Connection Issues
```bash
# Exec into pod
kubectl exec -it <pod-name> -n connectivity -- /bin/bash

# Test database connection
python manage.py dbshell

# Check environment variables
env | grep DB_
```

### Health Check Failing
```bash
# Port forward and test
kubectl port-forward <pod-name> -n connectivity 8000:8000

# Test endpoints
curl http://localhost:8000/health/live
curl http://localhost:8000/health/ready
curl http://localhost:8000/metrics
```

## 📊 Monitoring

### Resource Usage
```bash
# Pod metrics
kubectl top pods -n connectivity

# Node metrics
kubectl top nodes

# Describe deployment
kubectl describe deployment connectivity-service -n connectivity
```

### Application Metrics
```bash
# Port forward
kubectl port-forward svc/connectivity-service -n connectivity 8000:80

# View Prometheus metrics
curl http://localhost:8000/metrics
```

## 🔄 Git Workflow

### Feature Development
```bash
# Create feature branch
git checkout -b feature/my-feature

# Make changes and test locally
pytest apps/ -v

# Push and trigger CI
git push origin feature/my-feature

# Create PR to develop
```

### Release to Production
```bash
# Merge to main (triggers CD)
git checkout main
git merge develop
git push origin main

# Watch deployment
# GitHub Actions → CD pipeline → Kubernetes
```

## 🔐 Secrets Management

### Generate Secrets
```bash
# Django secret key
python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'

# JWT secret key
python3 -c 'import secrets; print(secrets.token_urlsafe(64))'
```

### Update Kubernetes Secrets
```bash
# Edit local secret file
nano k8s/base/secret.yaml.local

# Apply changes
kubectl apply -f k8s/base/secret.yaml.local

# Restart pods to pick up new secrets
kubectl rollout restart deployment/connectivity-service -n connectivity
```

## 📦 Image Management

### Docker Hub
```bash
# Login
docker login

# Tag image
docker tag connectivity-microservice:local yourusername/connectivity-microservice:v1.0.0

# Push
docker push yourusername/connectivity-microservice:v1.0.0
```

### Update Deployment Image
```bash
# Edit kustomization
cd k8s/overlays/production
kustomize edit set image connectivity-microservice=yourusername/connectivity-microservice:v1.0.0

# Apply
kubectl apply -k k8s/overlays/production
```

## 🧪 Testing

### Run Specific Tests
```bash
# Single test file
pytest apps/affiliation/tests.py -v

# Single test class
pytest apps/affiliation/tests.py::AffiliationServiceTests -v

# Single test method
pytest apps/affiliation/tests.py::AffiliationServiceTests::test_check_affiliation_citizen_found -v

# With coverage
pytest apps/affiliation/tests.py --cov=apps.affiliation --cov-report=html
```

### Test with Services
```bash
# Start services
docker-compose up -d db redis rabbitmq

# Run tests
pytest apps/ infrastructure/

# Stop services
docker-compose down
```

## 🆘 Emergency Procedures

### Rollback Production
```bash
# Quick rollback
kubectl rollout undo deployment/connectivity-service -n connectivity

# Rollback to specific revision
kubectl rollout history deployment/connectivity-service -n connectivity
kubectl rollout undo deployment/connectivity-service --to-revision=2 -n connectivity
```

### Scale Down (Emergency)
```bash
# Scale to 1 replica
kubectl scale deployment/connectivity-service --replicas=1 -n connectivity

# Scale to 0 (stop all)
kubectl scale deployment/connectivity-service --replicas=0 -n connectivity
```

### View Full Logs
```bash
# Last 100 lines
kubectl logs --tail=100 deployment/connectivity-service -n connectivity

# Follow logs from all pods
kubectl logs -f -l app=connectivity-service -n connectivity --all-containers=true

# Export logs to file
kubectl logs deployment/connectivity-service -n connectivity > service.log
```

## 📚 Useful Links

- **GitHub Actions**: https://github.com/YOUR_USERNAME/YOUR_REPO/actions
- **SonarCloud**: https://sonarcloud.io/dashboard?id=YOUR_PROJECT_KEY
- **Docker Hub**: https://hub.docker.com/r/YOUR_USERNAME/connectivity-microservice
- **Prometheus**: http://your-prometheus-url/targets
- **Grafana**: http://your-grafana-url/dashboards

---

**Tip**: Bookmark this file for quick reference!
