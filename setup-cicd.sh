#!/bin/bash
# Setup script for CI/CD and Kubernetes deployment
# This script helps configure the necessary components

set -e

echo "🚀 Connectivity Microservice - CI/CD Setup Script"
echo "=================================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
print_info "Checking prerequisites..."

command -v kubectl >/dev/null 2>&1 || {
    print_error "kubectl is not installed. Please install kubectl first."
    exit 1
}

command -v docker >/dev/null 2>&1 || {
    print_error "docker is not installed. Please install Docker first."
    exit 1
}

print_info "✅ Prerequisites check passed"
echo ""

# Collect configuration
print_info "Please provide the following information:"
echo ""

read -p "Docker Hub Username: " DOCKERHUB_USERNAME
read -p "SonarCloud Organization: " SONAR_ORG
read -p "SonarCloud Project Key: " SONAR_PROJECT_KEY

echo ""
print_info "Configuration received:"
echo "  Docker Hub: $DOCKERHUB_USERNAME"
echo "  SonarCloud Org: $SONAR_ORG"
echo "  SonarCloud Project: $SONAR_PROJECT_KEY"
echo ""

read -p "Is this correct? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_error "Setup cancelled."
    exit 1
fi

# Update sonar-project.properties
print_info "Updating sonar-project.properties..."
sed -i "s/REPLACE_WITH_YOUR_USERNAME_connectivity-microservice/$SONAR_PROJECT_KEY/" sonar-project.properties
sed -i "s/REPLACE_WITH_YOUR_ORGANIZATION/$SONAR_ORG/" sonar-project.properties
print_info "✅ SonarCloud configuration updated"

# Update base kustomization
print_info "Updating Kubernetes base configuration..."
sed -i "s/DOCKERHUB_USERNAME/$DOCKERHUB_USERNAME/" k8s/base/kustomization.yaml
print_info "✅ Kubernetes configuration updated"

# Create local secret template
print_info "Creating local secret template..."
cp k8s/base/secret.yaml k8s/base/secret.yaml.local

echo ""
print_warning "⚠️  IMPORTANT: You must edit k8s/base/secret.yaml.local with real values!"
print_warning "Replace all REPLACE_WITH_* placeholders with actual credentials."
echo ""

# Generate Django secret key
print_info "Generating Django secret key..."
DJANGO_SECRET=$(python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
print_info "Django Secret Key: $DJANGO_SECRET"
print_warning "Save this in a secure location!"

echo ""
print_info "Generating JWT secret key..."
JWT_SECRET=$(python3 -c 'import secrets; print(secrets.token_urlsafe(64))')
print_info "JWT Secret Key: $JWT_SECRET"
print_warning "Save this in a secure location!"

echo ""
echo "=================================================="
print_info "✅ Setup Complete!"
echo "=================================================="
echo ""
echo "Next steps:"
echo "1. Edit k8s/base/secret.yaml.local with real database/Redis/RabbitMQ credentials"
echo "2. Add GitHub Secrets in your repository:"
echo "   - SONAR_TOKEN (from https://sonarcloud.io/account/security)"
echo "   - DOCKERHUB_USERNAME (value: $DOCKERHUB_USERNAME)"
echo "   - DOCKERHUB_TOKEN (from https://hub.docker.com/settings/security)"
echo "   - KUBE_CONFIG (your kubeconfig file, base64 encoded)"
echo "   - SERVICE_URL (your service URL for health checks)"
echo ""
echo "3. Create Docker Hub repository: $DOCKERHUB_USERNAME/connectivity-microservice"
echo "4. Create SonarCloud project with key: $SONAR_PROJECT_KEY"
echo ""
echo "For detailed instructions, see:"
echo "  - CICD_DEPLOYMENT_GUIDE.md"
echo "  - CI_CD_IMPLEMENTATION_SUMMARY.md"
echo ""
print_info "Happy deploying! 🎉"
