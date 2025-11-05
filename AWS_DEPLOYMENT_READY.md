# AWS EKS Deployment - GitHub Secrets Configuration

## ✅ EKS Cluster Created Successfully!

**Cluster Name:** `connectivity-cluster`  
**Region:** `us-east-1`  
**Nodes:** 2 x t3.medium (Ready)  
**Kubernetes Version:** v1.32.9  

---

## 🔑 GitHub Secrets to Configure

Go to your GitHub repository: `https://github.com/alejandrodgz/project_connectivity/settings/secrets/actions`

Add the following secrets:

### 1. AWS Credentials (GitHub Actions User)
```
AWS_ACCESS_KEY_ID
Value: <use-the-access-key-id-provided-separately>

AWS_SECRET_ACCESS_KEY
Value: <use-the-secret-access-key-provided-separately>

AWS_REGION
Value: us-east-1

EKS_CLUSTER_NAME
Value: connectivity-cluster
```

**⚠️ IMPORTANT:** The actual AWS credentials were provided to you via terminal output.
Copy them from the terminal where we created the IAM access keys.

### 2. Docker Hub Credentials
You need to add your Docker Hub credentials:

```
DOCKERHUB_USERNAME
Value: <your-dockerhub-username>

DOCKERHUB_TOKEN
Value: <your-dockerhub-access-token>
```

**How to get Docker Hub token:**
1. Go to https://hub.docker.com/settings/security
2. Click "New Access Token"
3. Give it a name like "github-actions-connectivity"
4. Copy the token

### 3. SonarCloud Token (Already configured)
```
SONAR_TOKEN
Value: <already-configured>
```

---

## 📋 IAM User Details

**User:** `github-actions-connectivity`  
**ARN:** `arn:aws:iam::202508219818:user/github-actions-connectivity`  
**Policies Attached:**
- AmazonEKSClusterPolicy
- AmazonEC2ContainerRegistryPowerUser
- EKSDeploymentPolicy (custom)

**Kubernetes RBAC:** system:masters group (full access)

---

## 🚀 Next Steps

1. **Configure GitHub Secrets** (above)
2. **Update Kubernetes manifests** for production (optional: use RDS, ElastiCache, Amazon MQ)
3. **Push to GitHub** to trigger automated deployment
4. **Monitor deployment** in GitHub Actions

---

## 🔍 Verification Commands

After deployment, verify with:

```bash
# Check cluster
kubectl get nodes

# Check pods
kubectl get pods -n connectivity

# Check services
kubectl get svc -n connectivity

# Get LoadBalancer URL
kubectl get svc connectivity-app-nodeport -n connectivity -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'
```

---

## 💰 Cost Estimate

**Current Setup (Development):**
- EKS Control Plane: ~$73/month
- 2 x t3.medium nodes: ~$60/month (2 x $0.0416/hour)
- **Total: ~$133/month** (without LoadBalancer, RDS, etc.)

**With LoadBalancer:**
- Add ~$16/month for Classic Load Balancer
- **Total: ~$149/month**

---

## ⚠️ Important Notes

1. **Database:** Currently using MariaDB pod (ephemeral). For production, consider AWS RDS.
2. **Cache:** Currently using Redis pod (ephemeral). For production, consider AWS ElastiCache.
3. **Message Queue:** Currently using RabbitMQ pod. For production, consider Amazon MQ.
4. **Storage:** Pod data is ephemeral. Use AWS EBS volumes or RDS for persistence.
5. **Security:** Update secrets in k8s/secrets.yaml with production values before deploying.

---

## 🎯 Ready to Deploy!

Once GitHub Secrets are configured, just push your code:

```bash
git add .
git commit -m "Configure AWS EKS deployment"
git push origin master
```

The GitHub Actions workflow will automatically:
1. Build Docker image
2. Push to Docker Hub
3. Deploy to EKS
4. Run health checks
5. Rollback if deployment fails

---

**Cluster is ready and waiting for deployment! 🎉**
