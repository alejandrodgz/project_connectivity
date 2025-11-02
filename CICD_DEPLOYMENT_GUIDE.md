# CI/CD & Kubernetes Deployment Guide

## 🚀 Overview

This document provides comprehensive instructions for:
- Setting up CI/CD with GitHub Actions
- Deploying to Kubernetes using Kustomize
- Integrating with SonarCloud for code quality
- Managing secrets and configurations

## 📋 Prerequisites

### Required Accounts & Tools
- [ ] GitHub account with Actions enabled
- [ ] Docker Hub account
- [ ] SonarCloud account (https://sonarcloud.io)
- [ ] Kubernetes cluster (EKS, GKE, AKS, or Minikube for local)
- [ ] kubectl CLI installed
- [ ] kustomize CLI installed (optional, kubectl has built-in support)

### Required Secrets

Configure these secrets in your GitHub repository settings (Settings → Secrets and variables → Actions):

#### SonarCloud Secrets
- `SONAR_TOKEN`: Generate at https://sonarcloud.io/account/security

#### Docker Hub Secrets
- `DOCKERHUB_USERNAME`: Your Docker Hub username
- `DOCKERHUB_TOKEN`: Generate at https://hub.docker.com/settings/security

#### Kubernetes Secrets
- `KUBE_CONFIG`: Your Kubernetes cluster config (base64 encoded kubeconfig file)
- `SERVICE_URL`: Your deployed service URL (for health checks)

#### AWS Secrets (if using AWS)
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_REGION`

---

## 🛠️ Setup Instructions

### 1. SonarCloud Setup

1. **Create SonarCloud Organization**
   - Go to https://sonarcloud.io
   - Click "+" → "Create new organization"
   - Import your GitHub repository

2. **Update sonar-project.properties**
   ```properties
   sonar.projectKey=YOUR_USERNAME_connectivity-microservice
   sonar.organization=YOUR_ORGANIZATION
   ```

3. **Generate Token**
   - Go to https://sonarcloud.io/account/security
   - Generate a new token
   - Add it to GitHub secrets as `SONAR_TOKEN`

### 2. Docker Hub Setup

1. **Create Docker Hub Repository**
   ```bash
   # Login to Docker Hub
   docker login
   
   # Create repository (or do it via web interface)
   # Repository name: connectivity-microservice
   ```

2. **Generate Access Token**
   - Go to https://hub.docker.com/settings/security
   - Create new access token
   - Add to GitHub secrets as `DOCKERHUB_TOKEN`

3. **Update Kustomize Files**
   ```bash
   # Update base kustomization
   cd k8s/base
   # Edit kustomization.yaml and replace DOCKERHUB_USERNAME with your username
   ```

### 3. Kubernetes Setup

#### Option A: Local Development (Minikube)

```bash
# Start Minikube
minikube start --cpus=4 --memory=8192

# Enable metrics server
minikube addons enable metrics-server

# Deploy to local cluster
kubectl apply -k k8s/overlays/development

# Port forward to access locally
kubectl port-forward -n connectivity-dev svc/connectivity-service-dev 8000:80
```

#### Option B: Cloud Kubernetes (EKS/GKE/AKS)

1. **Configure kubectl**
   ```bash
   # AWS EKS
   aws eks update-kubeconfig --name your-cluster-name --region us-east-1
   
   # GKE
   gcloud container clusters get-credentials your-cluster-name --region us-central1
   
   # AKS
   az aks get-credentials --resource-group your-rg --name your-cluster-name
   ```

2. **Create Kubernetes Secrets**
   ```bash
   # Navigate to k8s directory
   cd k8s/base
   
   # Create actual secret file (DO NOT COMMIT THIS)
   cp secret.yaml secret.yaml.local
   
   # Edit secret.yaml.local with real values
   nano secret.yaml.local
   
   # Apply the secret
   kubectl apply -f secret.yaml.local
   ```

3. **Get kubeconfig for GitHub Actions**
   ```bash
   # Export kubeconfig
   cat ~/.kube/config | base64 -w 0
   
   # Add the output to GitHub secrets as KUBE_CONFIG
   ```

### 4. Update Kubernetes Secrets

Edit `k8s/base/secret.yaml.local` with real values:

```yaml
stringData:
  DB_HOST: "your-mariadb-host.rds.amazonaws.com"
  DB_USER: "connectivity_user"
  DB_PASSWORD: "your-secure-password"
  
  REDIS_HOST: "your-redis-host.cache.amazonaws.com"
  REDIS_PASSWORD: "your-redis-password"
  
  RABBITMQ_HOST: "your-rabbitmq-host.mq.amazonaws.com"
  RABBITMQ_USER: "connectivity"
  RABBITMQ_PASSWORD: "your-rabbitmq-password"
  
  SECRET_KEY: "generate-a-secure-django-secret-key-here"
  JWT_SECRET_KEY: "generate-a-different-secure-jwt-key-here"
```

**Generate secure keys:**
```bash
# Django secret key
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'

# JWT secret key
python -c 'import secrets; print(secrets.token_urlsafe(64))'
```

---

## 🔄 CI/CD Workflow

### Branch Strategy

```
main (production)
  ↑
  └── develop (staging)
       ↑
       └── feature/* (development)
```

### CI Pipeline (on develop/feature branches)

Triggers on: Push to `develop` or `feature/*` branches

**Steps:**
1. ✅ **Linting**
   - Black (code formatting)
   - isort (import sorting)
   - Flake8 (style guide)
   - Pylint (advanced linting)
   - Bandit (security scanning)

2. ✅ **Unit Tests**
   - Run all tests with pytest
   - Generate coverage report (target: >80%)
   - Upload artifacts

3. ✅ **Docker Build Validation**
   - Build Docker image (no push)
   - Validate Dockerfile

4. ✅ **SonarCloud Analysis**
   - Code quality metrics
   - Security vulnerabilities
   - Code smells
   - Technical debt

### CD Pipeline (on main branch)

Triggers on: Push to `main` branch

**Steps:**
1. 🐳 **Build & Push Docker Image**
   - Build multi-arch image
   - Tag with `main-<sha>` and `latest`
   - Push to Docker Hub

2. 📊 **SonarCloud Tracking**
   - Track main branch metrics

3. ☸️ **Deploy to Kubernetes**
   - Update image tag in kustomization
   - Apply production overlay
   - Wait for rollout
   - Verify deployment

4. ✅ **Health Check**
   - Verify service is responding
   - Run smoke tests

5. 🔄 **Rollback on Failure**
   - Automatic rollback if health check fails

---

## 📦 Deployment Commands

### Deploy to Development
```bash
kubectl apply -k k8s/overlays/development
kubectl rollout status deployment/connectivity-service-dev -n connectivity-dev
```

### Deploy to Staging
```bash
kubectl apply -k k8s/overlays/staging
kubectl rollout status deployment/connectivity-service-staging -n connectivity-staging
```

### Deploy to Production
```bash
kubectl apply -k k8s/overlays/production
kubectl rollout status deployment/connectivity-service -n connectivity
```

### View Resources
```bash
# Development
kubectl get all -n connectivity-dev

# Staging
kubectl get all -n connectivity-staging

# Production
kubectl get all -n connectivity
```

### View Logs
```bash
# Web service logs
kubectl logs -f deployment/connectivity-service -n connectivity

# Document consumer logs
kubectl logs -f deployment/connectivity-document-consumer -n connectivity

# Follow logs from all pods
kubectl logs -f -l app=connectivity-service -n connectivity --all-containers=true
```

### Scale Deployment
```bash
# Scale web service
kubectl scale deployment/connectivity-service --replicas=5 -n connectivity

# Scale consumer
kubectl scale deployment/connectivity-document-consumer --replicas=3 -n connectivity
```

### Rollback Deployment
```bash
# View rollout history
kubectl rollout history deployment/connectivity-service -n connectivity

# Rollback to previous version
kubectl rollout undo deployment/connectivity-service -n connectivity

# Rollback to specific revision
kubectl rollout undo deployment/connectivity-service --to-revision=2 -n connectivity
```

---

## 🔍 Monitoring & Debugging

### View Metrics
```bash
# Get resource usage
kubectl top pods -n connectivity
kubectl top nodes

# Describe deployment
kubectl describe deployment connectivity-service -n connectivity

# Get events
kubectl get events -n connectivity --sort-by='.lastTimestamp'
```

### Debug Pod Issues
```bash
# Get pod status
kubectl get pods -n connectivity

# Describe pod
kubectl describe pod <pod-name> -n connectivity

# Execute command in pod
kubectl exec -it <pod-name> -n connectivity -- /bin/bash

# Port forward for debugging
kubectl port-forward <pod-name> -n connectivity 8000:8000
```

### Check Health Endpoints
```bash
# Port forward service
kubectl port-forward svc/connectivity-service -n connectivity 8000:80

# Test health endpoints
curl http://localhost:8000/health/live
curl http://localhost:8000/health/ready
curl http://localhost:8000/metrics
```

---

## 🧪 Testing CI/CD Locally

### Test Docker Build
```bash
docker build -t connectivity-microservice:test .
docker run -p 8000:8000 --env-file .env.test connectivity-microservice:test
```

### Test Kustomize
```bash
# View generated manifests without applying
kubectl kustomize k8s/overlays/development

# Validate manifests
kubectl apply -k k8s/overlays/development --dry-run=client

# Apply to cluster
kubectl apply -k k8s/overlays/development
```

### Run Tests Locally
```bash
# Activate virtual environment
source env/bin/activate

# Run linting
black --check apps/ infrastructure/ settings/
flake8 apps/ infrastructure/ settings/
isort --check-only apps/ infrastructure/ settings/

# Run tests with coverage
pytest apps/ infrastructure/ --cov=apps --cov=infrastructure --cov-report=html

# View coverage report
open htmlcov/index.html
```

---

## 🔒 Security Best Practices

1. **Never commit secrets** to git
   - Use `.gitignore` for sensitive files
   - Use GitHub Secrets for CI/CD
   - Use Sealed Secrets or external secret managers for K8s

2. **Rotate secrets regularly**
   - Database passwords
   - JWT keys
   - API tokens

3. **Use RBAC** in Kubernetes
   - Minimal permissions for service accounts
   - Namespace isolation

4. **Enable security scanning**
   - Bandit for Python security issues
   - SonarCloud for vulnerabilities
   - Trivy for container scanning (optional)

---

## 📚 Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Kustomize Documentation](https://kustomize.io/)
- [SonarCloud Documentation](https://docs.sonarcloud.io/)
- [Django Deployment Checklist](https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/)

---

## 🆘 Troubleshooting

### CI Pipeline Fails

**Linting errors:**
```bash
# Auto-fix formatting
black apps/ infrastructure/ settings/
isort apps/ infrastructure/ settings/

# Check what's failing
flake8 apps/ infrastructure/ settings/
```

**Tests failing:**
```bash
# Run tests locally
pytest apps/ -v

# Run specific test
pytest apps/affiliation/tests.py::TestClassName::test_method_name -v
```

### CD Pipeline Fails

**Docker build fails:**
- Check Dockerfile syntax
- Verify all dependencies in requirements files
- Test build locally

**Kubernetes deployment fails:**
- Check secret values are correct
- Verify image tag exists in Docker Hub
- Check resource limits
- View pod logs: `kubectl logs <pod-name> -n connectivity`

**Health check fails:**
- Verify database connectivity
- Check RabbitMQ connection
- Review application logs
- Ensure migrations are run

---

## 📝 Checklist Before First Deployment

- [ ] SonarCloud project created and configured
- [ ] GitHub secrets configured (SONAR_TOKEN, DOCKERHUB_*, KUBE_CONFIG)
- [ ] Docker Hub repository created
- [ ] Kubernetes cluster accessible
- [ ] Database (MariaDB) provisioned and accessible
- [ ] Redis provisioned and accessible
- [ ] RabbitMQ provisioned and accessible
- [ ] Secrets created in Kubernetes with real values
- [ ] ConfigMap updated with correct endpoints
- [ ] DNS configured (for production)
- [ ] SSL certificates configured (for production)
- [ ] Monitoring configured (Prometheus/Grafana)

---

**Last Updated:** November 1, 2025  
**Maintained by:** DevOps Team
