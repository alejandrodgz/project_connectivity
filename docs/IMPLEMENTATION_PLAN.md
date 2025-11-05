# 🏗️ Citizen Affiliation Microservice - Implementation Plan

**Project**: Django Microservice for Citizen Affiliation & Document Authentication  
**Date Started**: October 30, 2025  
**Location**: `/home/alejo/connectivity/project_connectivity/`

---

## 📋 Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Technology Stack](#technology-stack)
4. [Project Structure](#project-structure)
5. [Implementation Steps](#implementation-steps)
6. [CI/CD Pipeline](#cicd-pipeline)
7. [Kubernetes Deployment](#kubernetes-deployment)
8. [Monitoring Setup](#monitoring-setup)
9. [Security & Authentication](#security--authentication)
10. [Progress Tracking](#progress-tracking)

---

## 🎯 Project Overview

### Main Functions

1. **Citizen Affiliation Checker**
   - Check external REST API to validate if a citizen can be affiliated
   - Validate eligibility criteria
   - Return affiliation status and details

2. **Document Authentication**
   - Authenticate and validate citizen documents
   - Process document verification requests
   - Publish events via RabbitMQ for other microservices

### Key Features

- ✅ RESTful API endpoints for external consumption
- ✅ Event-driven architecture using RabbitMQ
- ✅ JWT-based authentication for endpoint protection
- ✅ Complete CI/CD pipeline
- ✅ Kubernetes deployment with Kustomize
- ✅ Monitoring with Prometheus & Grafana
- ✅ Containerized with Docker
- ✅ Infrastructure as Code with Terraform (optional)

---

## 🏛️ Architecture

```
┌─────────────────────────────────────────────────────┐
│              API Gateway / Load Balancer             │
└──────────────────┬──────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────┐
│    Citizen Affiliation Microservice (Django)        │
│                                                      │
│  ┌────────────────────────────────────────────┐    │
│  │         REST API Endpoints                  │    │
│  │  • POST /api/affiliation/check             │    │
│  │  • POST /api/documents/authenticate        │    │
│  │  • POST /api/auth/login                    │    │
│  │  • GET  /api/health                        │    │
│  │  • GET  /metrics (Prometheus)              │    │
│  └─────────────────┬───────────────────────────┘    │
│                    │                                 │
│  ┌─────────────────▼───────────────────────────┐    │
│  │          Service Layer                      │    │
│  │  • AffiliationService                       │    │
│  │  • DocumentAuthService                      │    │
│  │  • EventPublisher                           │    │
│  └─────────────────┬───────────────────────────┘    │
│                    │                                 │
│  ┌─────────────────▼───────────────────────────┐    │
│  │        External Integrations                │    │
│  │  • External Affiliation API Client          │    │
│  │  • RabbitMQ Producer                        │    │
│  └─────────────────────────────────────────────┘    │
└──────────────────┬───────────────┬──────────────────┘
                   │               │
            ┌──────▼──────┐  ┌────▼──────────┐
            │  PostgreSQL │  │   RabbitMQ    │
            │  (Primary)  │  │ (Events Bus)  │
            └─────────────┘  └───────────────┘
                                     │
                   ┌─────────────────┴─────────────────┐
                   │                                   │
            ┌──────▼──────┐                    ┌──────▼──────┐
            │  Consumer   │                    │  Consumer   │
            │ Microservice│                    │ Microservice│
            │      #1     │                    │      #2     │
            └─────────────┘                    └─────────────┘
```

### Event Flow (RabbitMQ)

```
Affiliation MS ──publish──> RabbitMQ Exchange
                                   │
                    ┌──────────────┼──────────────┐
                    │              │              │
               Queue: affiliation  │         Queue: docs
                    │              │              │
              Consumer MS 1   Consumer MS 2  Consumer MS 3
```

---

## 🛠️ Technology Stack

### Backend
- **Framework**: Django 5.x + Django REST Framework
- **Language**: Python 3.12+
- **Database**: PostgreSQL 16
- **Message Broker**: RabbitMQ 3.12+
- **Cache**: Redis 7+ (for JWT blacklist)
- **Authentication**: JWT (djangorestframework-simplejwt)

### DevOps & Infrastructure
- **Containerization**: Docker
- **Orchestration**: Kubernetes (Minikube locally, EKS for production)
- **K8s Management**: Kustomize
- **CI/CD**: GitHub Actions
- **Monitoring**: Prometheus + Grafana
- **Logging**: ELK Stack (optional) or CloudWatch
- **IaC**: Terraform (optional, following auth-microservice pattern)

### Development Tools
- **Testing**: pytest, pytest-django, pytest-cov
- **Linting**: flake8, black, isort
- **Security**: bandit, safety
- **API Documentation**: drf-spectacular (OpenAPI/Swagger)

---

## 📁 Project Structure

```
project_connectivity/
├── manage.py
├── requirements/
│   ├── base.txt
│   ├── development.txt
│   ├── production.txt
│   └── testing.txt
├── settings/
│   ├── __init__.py
│   ├── settings.py
│   ├── asgi.py
│   ├── urls.py
│   └── wsgi.py
├── apps/
│   ├── __init__.py
│   ├── affiliation/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── serializers.py
│   │   ├── services.py
│   │   ├── urls.py
│   │   ├── tasks.py
│   │   └── tests/
│   ├── authentication/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── serializers.py
│   │   ├── urls.py
│   │   └── tests/
│   ├── documents/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── serializers.py
│   │   ├── services.py
│   │   ├── urls.py
│   │   └── tests/
│   └── core/
│       ├── __init__.py
│       ├── middleware.py
│       ├── exceptions.py
│       ├── utils.py
│       └── tests/
├── infrastructure/
│   ├── rabbitmq/
│   │   ├── __init__.py
│   │   ├── producer.py
│   │   ├── consumer.py
│   │   └── config.py
│   └── external_apis/
│       ├── __init__.py
│       ├── affiliation_client.py
│       └── base_client.py
├── docker/
│   ├── Dockerfile
│   ├── Dockerfile.dev
│   └── docker-compose.yml
├── k8s/
│   ├── base/
│   │   ├── kustomization.yaml
│   │   ├── namespace.yaml
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   ├── configmap.yaml
│   │   ├── secret.yaml (sealed)
│   │   ├── hpa.yaml
│   │   └── service-account.yaml
│   ├── overlays/
│   │   ├── development/
│   │   │   └── kustomization.yaml
│   │   ├── staging/
│   │   │   └── kustomization.yaml
│   │   └── production/
│   │       └── kustomization.yaml
│   └── terraform/ (optional)
│       ├── main.tf
│       ├── variables.tf
│       └── outputs.tf
├── monitoring/
│   ├── prometheus/
│   │   └── prometheus.yml
│   └── grafana/
│       └── dashboards/
│           └── django-dashboard.json
├── .github/
│   └── workflows/
│       ├── ci.yml
│       ├── cd.yml
│       └── security-scan.yml
├── tests/
│   ├── integration/
│   ├── e2e/
│   └── load/
├── docs/
│   ├── API.md
│   ├── DEPLOYMENT.md
│   └── TROUBLESHOOTING.md
├── .gitignore
├── .dockerignore
├── pytest.ini
├── setup.cfg
├── README.md
└── IMPLEMENTATION_PLAN.md (this file)
```

---

## 🚀 Implementation Steps

### Phase 1: Project Setup ✅

#### Step 1.1: Initialize Django Project
```bash
cd /home/alejo/connectivity/project_connectivity
source env/bin/activate

# Install base dependencies
pip install django djangorestframework djangorestframework-simplejwt
pip install psycopg2-binary pika redis celery
pip install django-prometheus django-cors-headers
pip install python-decouple django-environ

# Create requirements structure
mkdir requirements
pip freeze > requirements/base.txt
```

**Status**: ⏳ Pending

#### Step 1.2: Create Django Apps
```bash
cd /home/alejo/connectivity/project_connectivity
mkdir apps
python manage.py startapp affiliation apps/affiliation
python manage.py startapp authentication apps/authentication
python manage.py startapp documents apps/documents
python manage.py startapp core apps/core
```

**Status**: ⏳ Pending

#### Step 1.3: Configure Settings
- Split settings for different environments
- Configure database (PostgreSQL)
- Configure JWT authentication
- Configure CORS
- Configure Prometheus metrics

**Status**: ⏳ Pending

---

### Phase 2: Core Application Development

#### Step 2.1: Authentication App (JWT)
- [ ] User model customization
- [ ] JWT token generation
- [ ] Token refresh endpoint
- [ ] Token blacklist with Redis
- [ ] Login/logout endpoints
- [ ] Unit tests

**Files to create**:
- `apps/authentication/models.py`
- `apps/authentication/serializers.py`
- `apps/authentication/views.py`
- `apps/authentication/urls.py`
- `apps/authentication/tests/test_auth.py`

**Status**: ⏳ Pending

#### Step 2.2: Affiliation Checker App
- [ ] Create affiliation request model
- [ ] External API client implementation
- [ ] Affiliation check service
- [ ] REST endpoints
- [ ] Event publishing to RabbitMQ
- [ ] Unit tests

**Files to create**:
- `apps/affiliation/models.py`
- `apps/affiliation/serializers.py`
- `apps/affiliation/services.py`
- `apps/affiliation/views.py`
- `apps/affiliation/urls.py`
- `infrastructure/external_apis/affiliation_client.py`
- `apps/affiliation/tests/test_affiliation.py`

**API Endpoint**: `POST /api/v1/affiliation/check`

**Request Example**:
```json
{
  "citizen_id": "123456789",
  "document_type": "CC",
  "affiliation_type": "CONTRIBUTIVO"
}
```

**Response Example**:
```json
{
  "eligible": true,
  "citizen_id": "123456789",
  "affiliation_type": "CONTRIBUTIVO",
  "reason": "Citizen meets all requirements",
  "timestamp": "2025-10-30T10:00:00Z"
}
```

**RabbitMQ Event Published**:
```json
{
  "event_type": "affiliation.checked",
  "citizen_id": "123456789",
  "eligible": true,
  "timestamp": "2025-10-30T10:00:00Z"
}
```

**Status**: ⏳ Pending

#### Step 2.3: Document Authentication App
- [ ] Document model
- [ ] Document validation service
- [ ] Authentication logic
- [ ] REST endpoints
- [ ] Event publishing to RabbitMQ
- [ ] Unit tests

**Files to create**:
- `apps/documents/models.py`
- `apps/documents/serializers.py`
- `apps/documents/services.py`
- `apps/documents/views.py`
- `apps/documents/urls.py`
- `apps/documents/tests/test_documents.py`

**API Endpoint**: `POST /api/v1/documents/authenticate`

**Request Example**:
```json
{
  "document_number": "123456789",
  "document_type": "CC",
  "verification_code": "ABC123",
  "citizen_name": "John Doe"
}
```

**Response Example**:
```json
{
  "authenticated": true,
  "document_number": "123456789",
  "document_type": "CC",
  "verification_status": "VERIFIED",
  "timestamp": "2025-10-30T10:00:00Z"
}
```

**RabbitMQ Event Published**:
```json
{
  "event_type": "document.authenticated",
  "document_number": "123456789",
  "authenticated": true,
  "timestamp": "2025-10-30T10:00:00Z"
}
```

**Status**: ⏳ Pending

#### Step 2.4: RabbitMQ Integration
- [ ] RabbitMQ connection configuration
- [ ] Event producer implementation
- [ ] Event schemas definition
- [ ] Error handling and retries
- [ ] Integration tests

**Files to create**:
- `infrastructure/rabbitmq/config.py`
- `infrastructure/rabbitmq/producer.py`
- `infrastructure/rabbitmq/events.py`
- `infrastructure/rabbitmq/tests/test_producer.py`

**Status**: ⏳ Pending

#### Step 2.5: Health Checks & Metrics
- [ ] Liveness endpoint
- [ ] Readiness endpoint
- [ ] Prometheus metrics endpoint
- [ ] Custom business metrics

**Endpoints**:
- `GET /health/live`
- `GET /health/ready`
- `GET /metrics`

**Status**: ⏳ Pending

---

### Phase 3: Containerization

#### Step 3.1: Docker Setup
- [ ] Create Dockerfile (multi-stage build)
- [ ] Create docker-compose.yml
- [ ] PostgreSQL service
- [ ] RabbitMQ service
- [ ] Redis service
- [ ] Django application service
- [ ] Environment variables configuration

**Files to create**:
- `docker/Dockerfile`
- `docker/Dockerfile.dev`
- `docker/docker-compose.yml`
- `.dockerignore`

**Dockerfile Example** (following auth-microservice pattern):
```dockerfile
# Build stage
FROM python:3.12-slim as builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements/production.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r production.txt

# Runtime stage
FROM python:3.12-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy dependencies from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application
COPY . .

# Create non-root user
RUN useradd -m -u 1000 django && chown -R django:django /app
USER django

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s \
  CMD python -c "import requests; requests.get('http://localhost:8000/health/live')"

# Run application
CMD ["gunicorn", "settings.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4"]
```

**Status**: ⏳ Pending

#### Step 3.2: Local Testing with Docker Compose
```bash
cd /home/alejo/connectivity/project_connectivity
docker-compose up --build
```

**Status**: ⏳ Pending

---

### Phase 4: CI/CD Pipeline

#### Step 4.1: GitHub Actions - CI Pipeline

**File**: `.github/workflows/ci.yml`

**Jobs**:
1. **Lint** (flake8, black, isort)
2. **Security Scan** (bandit, safety)
3. **Unit Tests** (pytest with coverage)
4. **Integration Tests**
5. **Docker Build Validation**

**Status**: ⏳ Pending

#### Step 4.2: GitHub Actions - CD Pipeline

**File**: `.github/workflows/cd.yml`

**Jobs**:
1. **Build Docker Image**
2. **Push to Registry** (Docker Hub / ECR)
3. **Deploy to Kubernetes** (dev/staging/prod)
4. **Run Smoke Tests**
5. **Notify deployment status**

**Status**: ⏳ Pending

#### Step 4.3: Security Scanning

**File**: `.github/workflows/security-scan.yml`

**Scans**:
- Dependency vulnerabilities (safety, pip-audit)
- Code security issues (bandit)
- Docker image scanning (Trivy)
- SAST (SonarQube optional)

**Status**: ⏳ Pending

---

### Phase 5: Kubernetes Deployment

#### Step 5.1: Base Kubernetes Manifests

**Files to create**:
- `k8s/base/namespace.yaml`
- `k8s/base/deployment.yaml`
- `k8s/base/service.yaml`
- `k8s/base/configmap.yaml`
- `k8s/base/secret.yaml` (use Sealed Secrets)
- `k8s/base/hpa.yaml` (Horizontal Pod Autoscaler)
- `k8s/base/service-account.yaml`
- `k8s/base/kustomization.yaml`

**Deployment Configuration**:
```yaml
replicas: 3
resources:
  requests:
    memory: "256Mi"
    cpu: "250m"
  limits:
    memory: "512Mi"
    cpu: "500m"
```

**Status**: ⏳ Pending

#### Step 5.2: Kustomize Overlays

Create environment-specific configurations:
- Development overlay
- Staging overlay
- Production overlay

**Status**: ⏳ Pending

#### Step 5.3: External Dependencies (PostgreSQL, RabbitMQ, Redis)

**Options**:
1. **Managed Services** (Recommended for production):
   - RDS for PostgreSQL
   - Amazon MQ for RabbitMQ
   - ElastiCache for Redis

2. **In-cluster** (For development):
   - Helm charts for each service
   - StatefulSets with persistent volumes

**Status**: ⏳ Pending

#### Step 5.4: Ingress Configuration

**File**: `k8s/base/ingress.yaml`

Configure:
- TLS/SSL certificates
- Path-based routing
- Rate limiting

**Status**: ⏳ Pending

---

### Phase 6: Monitoring & Observability

#### Step 6.1: Prometheus Setup

**Files**:
- `monitoring/prometheus/prometheus.yml`
- `k8s/monitoring/prometheus-deployment.yaml`
- `k8s/monitoring/prometheus-service.yaml`

**Metrics to collect**:
- Request latency
- Request rate
- Error rate
- Database connection pool
- RabbitMQ queue depth
- Custom business metrics (affiliations checked, documents authenticated)

**Status**: ⏳ Pending

#### Step 6.2: Grafana Setup

**Files**:
- `k8s/monitoring/grafana-deployment.yaml`
- `k8s/monitoring/grafana-service.yaml`
- `monitoring/grafana/dashboards/django-dashboard.json`

**Dashboards**:
- Application metrics
- Infrastructure metrics
- Business metrics
- Alerts configuration

**Status**: ⏳ Pending

#### Step 6.3: Logging

**Options**:
1. ELK Stack (Elasticsearch, Logstash, Kibana)
2. CloudWatch Logs (AWS)
3. Loki + Grafana

**Status**: ⏳ Pending

#### Step 6.4: Alerting

Configure alerts for:
- High error rate
- High latency
- Service down
- Database connection issues
- RabbitMQ queue buildup

**Status**: ⏳ Pending

---

### Phase 7: Testing

#### Step 7.1: Unit Tests
- Models tests
- Serializers tests
- Service layer tests
- View tests
- Target: >80% code coverage

**Status**: ⏳ Pending

#### Step 7.2: Integration Tests
- API endpoint tests
- Database integration tests
- RabbitMQ integration tests
- External API mock tests

**Status**: ⏳ Pending

#### Step 7.3: E2E Tests
- Full workflow tests
- Authentication flow
- Affiliation check flow
- Document authentication flow

**Status**: ⏳ Pending

#### Step 7.4: Load Tests
- Using locust or k6
- Test 1000+ concurrent requests
- Identify bottlenecks

**Status**: ⏳ Pending

---

### Phase 8: Documentation

#### Step 8.1: API Documentation
- OpenAPI/Swagger with drf-spectacular
- Request/response examples
- Authentication guide
- Error codes reference

**Status**: ⏳ Pending

#### Step 8.2: Deployment Documentation
- Local setup guide
- Docker setup guide
- Kubernetes deployment guide
- Environment variables reference

**Status**: ⏳ Pending

#### Step 8.3: Architecture Documentation
- System architecture diagrams
- Sequence diagrams
- Database schema
- Event flow diagrams

**Status**: ⏳ Pending

---

## 🔐 Security & Authentication

### JWT Implementation

**Dependencies**:
```bash
pip install djangorestframework-simplejwt
```

**Settings Configuration**:
```python
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
}
```

**Protected Endpoints**:
- All `/api/v1/affiliation/*` endpoints
- All `/api/v1/documents/*` endpoints

**Public Endpoints**:
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `GET /health/*`
- `GET /metrics`

**Status**: ⏳ Pending

---

## 📊 Progress Tracking

### Current Phase: **Phase 1 - Project Setup**

### Completed Tasks
- [x] Research existing auth-microservice architecture
- [x] Create comprehensive implementation plan
- [ ] Initialize Django project structure
- [ ] Set up virtual environment
- [ ] Install base dependencies

### Next Steps
1. Set up Django project with proper structure
2. Configure settings for multiple environments
3. Create Django apps (affiliation, authentication, documents, core)
4. Implement JWT authentication
5. Develop affiliation checker service

### Blockers
- None currently

### Notes
- Following auth-microservice pattern from `/home/alejo/Kris/auth-microservice`
- Using Kustomize for Kubernetes management
- Prometheus + Grafana for monitoring
- RabbitMQ for event-driven communication
- JWT for API authentication

---

## 🔗 References

### External Resources
- [Django REST Framework](https://www.django-rest-framework.org/)
- [djangorestframework-simplejwt](https://django-rest-framework-simplejwt.readthedocs.io/)
- [Pika (RabbitMQ Python Client)](https://pika.readthedocs.io/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Kustomize](https://kustomize.io/)
- [Prometheus Django Exporter](https://github.com/korfuri/django-prometheus)

### Internal Resources
- Auth Microservice Reference: `/home/alejo/Kris/auth-microservice`
- Project Location: `/home/alejo/connectivity/project_connectivity/`

---

## 📝 Change Log

| Date | Phase | Change | Author |
|------|-------|--------|--------|
| 2025-10-30 | Planning | Initial implementation plan created | AI Assistant |

---

## 🎯 Success Criteria

- [ ] All REST endpoints functional and tested
- [ ] JWT authentication working correctly
- [ ] RabbitMQ events publishing successfully
- [ ] CI/CD pipeline passing all checks
- [ ] Kubernetes deployment successful
- [ ] Prometheus metrics exposed and collected
- [ ] Grafana dashboards operational
- [ ] >80% test coverage
- [ ] API documentation complete
- [ ] Load tests passing (1000+ concurrent requests)

---

**Last Updated**: October 30, 2025  
**Document Version**: 1.0  
**Status**: 🟡 In Progress
