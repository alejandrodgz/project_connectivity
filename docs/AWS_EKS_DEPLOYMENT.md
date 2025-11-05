# AWS EKS Deployment Guide

This guide will help you deploy the Connectivity Microservice to Amazon EKS (Elastic Kubernetes Service).

## 📋 Prerequisites

1. **AWS Account** with appropriate permissions
2. **AWS CLI** installed and configured
3. **kubectl** installed (v1.28+)
4. **eksctl** installed (for easy EKS cluster creation)
5. **Docker Hub account** (for container images)

## 🚀 Step 1: Create EKS Cluster

### Option A: Using eksctl (Recommended for Quick Setup)

```bash
# Install eksctl (if not installed)
curl --silent --location "https://github.com/weaveworks/eksctl/releases/latest/download/eksctl_$(uname -s)_amd64.tar.gz" | tar xz -C /tmp
sudo mv /tmp/eksctl /usr/local/bin

# Create EKS cluster
eksctl create cluster \
  --name connectivity-cluster \
  --region us-east-1 \
  --nodegroup-name connectivity-nodes \
  --node-type t3.medium \
  --nodes 2 \
  --nodes-min 1 \
  --nodes-max 3 \
  --managed
```

### Option B: Using AWS Console

1. Go to **EKS** service in AWS Console
2. Click **Add cluster** → **Create**
3. Configure:
   - **Name**: connectivity-cluster
   - **Kubernetes version**: 1.28
   - **Cluster service role**: Create or select existing
4. Configure **Networking**:
   - Select VPC and subnets
   - Choose cluster endpoint access: Public and private
5. Create **Node Group**:
   - **Name**: connectivity-nodes
   - **Instance type**: t3.medium
   - **Scaling configuration**: Min 1, Max 3, Desired 2

## 🔧 Step 2: Configure kubectl

```bash
# Update kubeconfig to connect to your EKS cluster
aws eks update-kubeconfig --region us-east-1 --name connectivity-cluster

# Verify connection
kubectl get nodes
```

## 🔐 Step 3: Set up GitHub Secrets

Add these secrets to your GitHub repository (Settings → Secrets and variables → Actions):

| Secret Name | Description | Example |
|-------------|-------------|---------|
| `AWS_ACCESS_KEY_ID` | AWS Access Key | AKIA... |
| `AWS_SECRET_ACCESS_KEY` | AWS Secret Key | wJalr... |
| `AWS_REGION` | AWS Region | us-east-1 |
| `EKS_CLUSTER_NAME` | EKS Cluster Name | connectivity-cluster |
| `DOCKERHUB_USERNAME` | Docker Hub username | yourusername |
| `DOCKERHUB_TOKEN` | Docker Hub access token | dckr_pat_... |
| `SONAR_TOKEN` | SonarCloud token (optional) | sqp_... |

### How to get AWS credentials:

```bash
# Create IAM user for GitHub Actions
aws iam create-user --user-name github-actions-connectivity

# Attach policies
aws iam attach-user-policy \
  --user-name github-actions-connectivity \
  --policy-arn arn:aws:iam::aws:policy/AmazonEKSClusterPolicy

aws iam attach-user-policy \
  --user-name github-actions-connectivity \
  --policy-arn arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy

# Create access key
aws iam create-access-key --user-name github-actions-connectivity
```

## 📦 Step 4: Update Kubernetes Secrets

Update the `k8s/secrets.yaml` file with production values:

```bash
# Encode your secrets in base64
echo -n "your-production-password" | base64

# Update k8s/secrets.yaml with encoded values
```

**Important**: Never commit real secrets to git! Use GitHub Secrets or AWS Secrets Manager.

## 🌐 Step 5: Expose Services with LoadBalancer

### Option A: Using AWS Load Balancer Controller (Recommended)

```bash
# Install AWS Load Balancer Controller
eksctl utils associate-iam-oidc-provider --cluster connectivity-cluster --region us-east-1 --approve

# Create IAM policy
curl -o iam-policy.json https://raw.githubusercontent.com/kubernetes-sigs/aws-load-balancer-controller/main/docs/install/iam_policy.json

aws iam create-policy \
  --policy-name AWSLoadBalancerControllerIAMPolicy \
  --policy-document file://iam-policy.json

# Create service account
eksctl create iamserviceaccount \
  --cluster=connectivity-cluster \
  --namespace=kube-system \
  --name=aws-load-balancer-controller \
  --attach-policy-arn=arn:aws:iam::<ACCOUNT_ID>:policy/AWSLoadBalancerControllerIAMPolicy \
  --approve

# Install the controller
kubectl apply -k "github.com/aws/eks-charts/stable/aws-load-balancer-controller//crds?ref=master"

helm repo add eks https://aws.github.io/eks-charts
helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system \
  --set clusterName=connectivity-cluster \
  --set serviceAccount.create=false \
  --set serviceAccount.name=aws-load-balancer-controller
```

### Update app.yaml to use LoadBalancer:

```yaml
---
apiVersion: v1
kind: Service
metadata:
  name: connectivity-app-lb
  namespace: connectivity
  annotations:
    service.beta.kubernetes.io/aws-load-balancer-type: "nlb"
    service.beta.kubernetes.io/aws-load-balancer-scheme: "internet-facing"
spec:
  type: LoadBalancer
  selector:
    app: connectivity-app
  ports:
  - port: 80
    targetPort: 8000
    protocol: TCP
```

### Option B: Using Ingress with ALB

Create an Ingress resource:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: connectivity-ingress
  namespace: connectivity
  annotations:
    kubernetes.io/ingress.class: alb
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
spec:
  rules:
  - http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: connectivity-app
            port:
              number: 8000
```

## 🗄️ Step 6: Set up RDS for Production Database (Optional but Recommended)

Instead of running MariaDB in Kubernetes, use AWS RDS:

```bash
# Create RDS MariaDB instance
aws rds create-db-instance \
  --db-instance-identifier connectivity-db \
  --db-instance-class db.t3.micro \
  --engine mariadb \
  --master-username admin \
  --master-user-password <strong-password> \
  --allocated-storage 20 \
  --vpc-security-group-ids sg-xxxxx \
  --db-subnet-group-name connectivity-db-subnet
```

Update `k8s/configmap.yaml`:
```yaml
data:
  DB_HOST: "connectivity-db.xxxxx.us-east-1.rds.amazonaws.com"
  DB_PORT: "3306"
```

## 📊 Step 7: Set up ElastiCache for Redis (Optional)

```bash
# Create ElastiCache Redis cluster
aws elasticache create-cache-cluster \
  --cache-cluster-id connectivity-redis \
  --cache-node-type cache.t3.micro \
  --engine redis \
  --num-cache-nodes 1 \
  --security-group-ids sg-xxxxx \
  --subnet-group-name connectivity-cache-subnet
```

Update `k8s/configmap.yaml`:
```yaml
data:
  REDIS_HOST: "connectivity-redis.xxxxx.cache.amazonaws.com"
  REDIS_PORT: "6379"
```

## 🔐 Step 8: Set up Amazon MQ for RabbitMQ (Optional)

```bash
# Create Amazon MQ broker
aws mq create-broker \
  --broker-name connectivity-mq \
  --deployment-mode SINGLE_INSTANCE \
  --engine-type RABBITMQ \
  --engine-version 3.11.20 \
  --host-instance-type mq.t3.micro \
  --publicly-accessible \
  --users Username=admin,Password=<strong-password>
```

## 🚀 Step 9: Deploy Application

### Manual Deployment:

```bash
# Apply all manifests
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/mariadb.yaml
kubectl apply -f k8s/redis.yaml
kubectl apply -f k8s/rabbitmq.yaml
kubectl apply -f k8s/app.yaml
kubectl apply -f k8s/consumer.yaml

# Check deployment status
kubectl get all -n connectivity
```

### CI/CD Deployment:

Simply push to `main` or `master` branch, and GitHub Actions will:
1. Build Docker image
2. Push to Docker Hub
3. Deploy to EKS
4. Run health checks
5. Rollback if health checks fail

## 📋 Step 10: Verify Deployment

```bash
# Check pods
kubectl get pods -n connectivity

# Check services
kubectl get svc -n connectivity

# Get LoadBalancer URL
kubectl get svc connectivity-app-lb -n connectivity -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'

# Test health endpoint
LB_URL=$(kubectl get svc connectivity-app-lb -n connectivity -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
curl http://${LB_URL}/health/

# Check logs
kubectl logs -n connectivity deployment/connectivity-app --tail=50
kubectl logs -n connectivity deployment/connectivity-consumer --tail=50
```

## 🔍 Monitoring & Observability

### CloudWatch Container Insights

```bash
# Install CloudWatch agent
kubectl apply -f https://raw.githubusercontent.com/aws-samples/amazon-cloudwatch-container-insights/latest/k8s-deployment-manifest-templates/deployment-mode/daemonset/container-insights-monitoring/quickstart/cwagent-fluentd-quickstart.yaml
```

### Prometheus Metrics

Your app already exposes `/metrics` endpoint. Set up Prometheus in a separate namespace:

```bash
# Install Prometheus using Helm
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/kube-prometheus-stack -n monitoring --create-namespace
```

## 💰 Cost Optimization

1. **Use Spot Instances for non-critical workloads**
2. **Enable Cluster Autoscaler**
3. **Right-size your instances** (start with t3.medium, monitor and adjust)
4. **Use RDS/ElastiCache Reserved Instances** for long-term savings
5. **Set up pod resource limits** to avoid overprovisioning

## 🔒 Security Best Practices

1. **Enable encryption at rest** for RDS and EBS volumes
2. **Use AWS Secrets Manager** instead of K8s secrets for sensitive data
3. **Enable VPC Flow Logs**
4. **Set up Security Groups** properly
5. **Use IAM roles for service accounts** (IRSA)
6. **Enable EKS audit logging**

## 🆘 Troubleshooting

### Pods not starting:
```bash
kubectl describe pod <pod-name> -n connectivity
kubectl logs <pod-name> -n connectivity
```

### Service not accessible:
```bash
kubectl get svc -n connectivity
kubectl describe svc connectivity-app-lb -n connectivity
```

### Database connection issues:
```bash
# Test from inside pod
kubectl exec -it deployment/connectivity-app -n connectivity -- python manage.py dbshell
```

## 📚 Additional Resources

- [EKS Best Practices Guide](https://aws.github.io/aws-eks-best-practices/)
- [AWS Load Balancer Controller](https://kubernetes-sigs.github.io/aws-load-balancer-controller/)
- [EKS Workshop](https://www.eksworkshop.com/)
