# Documentation Index

Welcome to the Connectivity Microservice documentation. This index will help you find the right documentation for your needs.

## 📚 Table of Contents

### Getting Started
- **[Quick Start Guide](QUICK_START.md)** - Get up and running quickly
- **[README](../README.md)** - Project overview and setup instructions

### Development
- **[Affiliation Implementation Summary](AFFILIATION_IMPLEMENTATION_SUMMARY.md)** - Core feature implementation details
- **[Implementation Plan](IMPLEMENTATION_PLAN.md)** - Original development plan and milestones

### CI/CD & Deployment
- **[CI/CD Implementation Summary](CI_CD_IMPLEMENTATION_SUMMARY.md)** - Overview of CI/CD pipeline
- **[CI/CD Deployment Guide](CICD_DEPLOYMENT_GUIDE.md)** - Detailed deployment procedures
- **[CI/CD Quick Reference](CICD_QUICK_REFERENCE.md)** - Common commands and troubleshooting
- **[Project Status](PROJECT_STATUS.md)** - Current project status and next steps

### Kubernetes
- **[K8s Local Testing](K8S_LOCAL_TESTING.md)** - Testing Kubernetes deployments locally
- **[RabbitMQ K8s Fix](RABBITMQ_K8S_FIX.md)** - RabbitMQ deployment troubleshooting

### Security & Authentication
- **[Production User Management](PRODUCTION_USER_MANAGEMENT.md)** - How admin users are created in production
- **[Service-to-Service Authentication](SERVICE_TO_SERVICE_AUTH.md)** - How external services authenticate and consume the API

### Integration
- **[External Service Integration](EXTERNAL_SERVICE_INTEGRATION.md)** - Integration guide for external services
- **[Document Authentication](DOCUMENT_AUTHENTICATION.md)** - Document authentication flow

### Administration
- **[Admin Guide](ADMIN_GUIDE.md)** - Administrator reference
- **[Quick Reference](QUICK_REFERENCE.md)** - Admin quick reference guide

---

## 📖 Documentation by Role

### For Developers
1. [Quick Start Guide](QUICK_START.md) - Setup development environment
2. [Affiliation Implementation Summary](AFFILIATION_IMPLEMENTATION_SUMMARY.md) - Understand core features
3. [CI/CD Quick Reference](CICD_QUICK_REFERENCE.md) - Daily commands
4. [K8s Local Testing](K8S_LOCAL_TESTING.md) - Test locally with Kubernetes

### For DevOps Engineers
1. [CI/CD Implementation Summary](CI_CD_IMPLEMENTATION_SUMMARY.md) - Pipeline architecture
2. [CI/CD Deployment Guide](CICD_DEPLOYMENT_GUIDE.md) - Deployment procedures
3. [Production User Management](PRODUCTION_USER_MANAGEMENT.md) - User creation strategies
4. [RabbitMQ K8s Fix](RABBITMQ_K8S_FIX.md) - Troubleshooting guide

### For External Service Teams
1. [Service-to-Service Authentication](SERVICE_TO_SERVICE_AUTH.md) - How to authenticate
2. [External Service Integration](EXTERNAL_SERVICE_INTEGRATION.md) - Integration patterns
3. [Document Authentication](DOCUMENT_AUTHENTICATION.md) - Document flow

### For System Administrators
1. [Admin Guide](ADMIN_GUIDE.md) - Administration tasks
2. [Quick Reference](QUICK_REFERENCE.md) - Common operations
3. [Production User Management](PRODUCTION_USER_MANAGEMENT.md) - User management

---

## 🔍 Find What You Need

### "How do I..."

#### ...set up my development environment?
→ [Quick Start Guide](QUICK_START.md)

#### ...deploy to production?
→ [CI/CD Deployment Guide](CICD_DEPLOYMENT_GUIDE.md)

#### ...test Kubernetes locally?
→ [K8s Local Testing](K8S_LOCAL_TESTING.md)

#### ...create admin users in production?
→ [Production User Management](PRODUCTION_USER_MANAGEMENT.md)

#### ...integrate my external service?
→ [Service-to-Service Authentication](SERVICE_TO_SERVICE_AUTH.md)  
→ [External Service Integration](EXTERNAL_SERVICE_INTEGRATION.md)

#### ...troubleshoot RabbitMQ in Kubernetes?
→ [RabbitMQ K8s Fix](RABBITMQ_K8S_FIX.md)

#### ...understand the affiliation check feature?
→ [Affiliation Implementation Summary](AFFILIATION_IMPLEMENTATION_SUMMARY.md)

#### ...see what's been completed?
→ [Project Status](PROJECT_STATUS.md)

---

## 📋 Documentation Categories

### Architecture & Design
- [Implementation Plan](IMPLEMENTATION_PLAN.md)
- [Affiliation Implementation Summary](AFFILIATION_IMPLEMENTATION_SUMMARY.md)
- [Document Authentication](DOCUMENT_AUTHENTICATION.md)

### Operations
- [CI/CD Implementation Summary](CI_CD_IMPLEMENTATION_SUMMARY.md)
- [CI/CD Deployment Guide](CICD_DEPLOYMENT_GUIDE.md)
- [CI/CD Quick Reference](CICD_QUICK_REFERENCE.md)
- [K8s Local Testing](K8S_LOCAL_TESTING.md)
- [RabbitMQ K8s Fix](RABBITMQ_K8S_FIX.md)

### Security
- [Production User Management](PRODUCTION_USER_MANAGEMENT.md)
- [Service-to-Service Authentication](SERVICE_TO_SERVICE_AUTH.md)

### Integration
- [External Service Integration](EXTERNAL_SERVICE_INTEGRATION.md)
- [Document Authentication](DOCUMENT_AUTHENTICATION.md)

### Reference
- [Admin Guide](ADMIN_GUIDE.md)
- [Quick Reference](QUICK_REFERENCE.md)
- [CI/CD Quick Reference](CICD_QUICK_REFERENCE.md)
- [Project Status](PROJECT_STATUS.md)

---

## 🆘 Need Help?

- Check the [Quick Reference](QUICK_REFERENCE.md) for common tasks
- See [CI/CD Quick Reference](CICD_QUICK_REFERENCE.md) for deployment commands
- Review [Project Status](PROJECT_STATUS.md) for current state
- Read [Troubleshooting sections](#) in relevant guides

---

## 🔄 Keeping Documentation Updated

When adding new documentation:
1. Create the `.md` file in the `/docs` folder
2. Add it to this index under appropriate categories
3. Link it from relevant existing documents
4. Update the "Find What You Need" section if applicable

**Note:** Only `README.md` should remain in the project root. All other documentation belongs in `/docs`.
