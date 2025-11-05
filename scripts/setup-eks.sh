#!/bin/bash

# AWS EKS Quick Setup Script
# This script helps set up the basic infrastructure for deploying to AWS EKS

set -e

echo "=========================================="
echo "🚀 AWS EKS Setup for Connectivity Service"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI is not installed. Please install it first:${NC}"
    echo "https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"
    exit 1
fi

# Check if kubectl is installed
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}❌ kubectl is not installed. Please install it first:${NC}"
    echo "https://kubernetes.io/docs/tasks/tools/"
    exit 1
fi

# Check if eksctl is installed
if ! command -v eksctl &> /dev/null; then
    echo -e "${YELLOW}⚠️  eksctl is not installed. Installing now...${NC}"
    curl --silent --location "https://github.com/weaveworks/eksctl/releases/latest/download/eksctl_$(uname -s)_amd64.tar.gz" | tar xz -C /tmp
    sudo mv /tmp/eksctl /usr/local/bin
    echo -e "${GREEN}✅ eksctl installed${NC}"
fi

echo ""
echo "Step 1: Configuration"
echo "--------------------"

# Get cluster configuration
read -p "Enter AWS Region (default: us-east-1): " AWS_REGION
AWS_REGION=${AWS_REGION:-us-east-1}

read -p "Enter EKS Cluster Name (default: connectivity-cluster): " CLUSTER_NAME
CLUSTER_NAME=${CLUSTER_NAME:-connectivity-cluster}

read -p "Enter Node Instance Type (default: t3.medium): " INSTANCE_TYPE
INSTANCE_TYPE=${INSTANCE_TYPE:-t3.medium}

read -p "Enter Minimum Nodes (default: 1): " MIN_NODES
MIN_NODES=${MIN_NODES:-1}

read -p "Enter Maximum Nodes (default: 3): " MAX_NODES
MAX_NODES=${MAX_NODES:-3}

read -p "Enter Desired Nodes (default: 2): " DESIRED_NODES
DESIRED_NODES=${DESIRED_NODES:-2}

echo ""
echo -e "${GREEN}Configuration:${NC}"
echo "  Region: $AWS_REGION"
echo "  Cluster: $CLUSTER_NAME"
echo "  Instance Type: $INSTANCE_TYPE"
echo "  Nodes: $MIN_NODES - $MAX_NODES (desired: $DESIRED_NODES)"
echo ""

read -p "Proceed with cluster creation? (y/n): " CONFIRM
if [ "$CONFIRM" != "y" ]; then
    echo "Aborted."
    exit 0
fi

echo ""
echo "Step 2: Creating EKS Cluster"
echo "----------------------------"
echo -e "${YELLOW}⏳ This may take 15-20 minutes...${NC}"

eksctl create cluster \
  --name $CLUSTER_NAME \
  --region $AWS_REGION \
  --nodegroup-name connectivity-nodes \
  --node-type $INSTANCE_TYPE \
  --nodes $DESIRED_NODES \
  --nodes-min $MIN_NODES \
  --nodes-max $MAX_NODES \
  --managed

echo ""
echo -e "${GREEN}✅ EKS Cluster created successfully!${NC}"

echo ""
echo "Step 3: Configuring kubectl"
echo "--------------------------"

aws eks update-kubeconfig --region $AWS_REGION --name $CLUSTER_NAME

echo -e "${GREEN}✅ kubectl configured${NC}"

echo ""
echo "Step 4: Verifying Cluster"
echo "------------------------"

kubectl get nodes

echo ""
echo "Step 5: Creating IAM User for GitHub Actions"
echo "--------------------------------------------"

IAM_USER="github-actions-$CLUSTER_NAME"

# Check if user exists
if aws iam get-user --user-name $IAM_USER &> /dev/null; then
    echo -e "${YELLOW}⚠️  IAM user $IAM_USER already exists${NC}"
else
    aws iam create-user --user-name $IAM_USER
    echo -e "${GREEN}✅ IAM user created${NC}"
fi

# Attach policies
aws iam attach-user-policy \
  --user-name $IAM_USER \
  --policy-arn arn:aws:iam::aws:policy/AmazonEKSClusterPolicy || true

aws iam attach-user-policy \
  --user-name $IAM_USER \
  --policy-arn arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy || true

echo ""
echo "Creating access key..."
ACCESS_KEY_OUTPUT=$(aws iam create-access-key --user-name $IAM_USER 2>/dev/null || echo "exists")

if [ "$ACCESS_KEY_OUTPUT" != "exists" ]; then
    AWS_ACCESS_KEY_ID=$(echo $ACCESS_KEY_OUTPUT | jq -r '.AccessKey.AccessKeyId')
    AWS_SECRET_ACCESS_KEY=$(echo $ACCESS_KEY_OUTPUT | jq -r '.AccessKey.SecretAccessKey')
    
    echo ""
    echo -e "${GREEN}✅ Access keys created${NC}"
    echo ""
    echo "=========================================="
    echo "🔐 GitHub Secrets Configuration"
    echo "=========================================="
    echo ""
    echo "Add these secrets to your GitHub repository:"
    echo "(Settings → Secrets and variables → Actions → New repository secret)"
    echo ""
    echo -e "${YELLOW}AWS_ACCESS_KEY_ID:${NC}"
    echo "$AWS_ACCESS_KEY_ID"
    echo ""
    echo -e "${YELLOW}AWS_SECRET_ACCESS_KEY:${NC}"
    echo "$AWS_SECRET_ACCESS_KEY"
    echo ""
    echo -e "${YELLOW}AWS_REGION:${NC}"
    echo "$AWS_REGION"
    echo ""
    echo -e "${YELLOW}EKS_CLUSTER_NAME:${NC}"
    echo "$CLUSTER_NAME"
    echo ""
    echo -e "${RED}⚠️  IMPORTANT: Save these credentials securely! They won't be shown again.${NC}"
else
    echo -e "${YELLOW}⚠️  Access key already exists for this user. Use existing credentials or delete and recreate.${NC}"
fi

echo ""
echo "=========================================="
echo "🎉 Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. ✅ Add the above secrets to your GitHub repository"
echo "2. ✅ Review and update k8s/secrets.yaml with production values"
echo "3. ✅ Push to main/master branch to trigger deployment"
echo "4. ✅ Monitor deployment: kubectl get all -n connectivity"
echo ""
echo "To delete the cluster later:"
echo "  eksctl delete cluster --name $CLUSTER_NAME --region $AWS_REGION"
echo ""
