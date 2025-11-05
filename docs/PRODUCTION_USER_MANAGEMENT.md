# Production User Management - Best Practices

## ❌ What NOT to Do

**Never manually SSH/exec into production instances to create users!**

```bash
# ❌ WRONG - Don't do this in production
kubectl exec -it pod/app -- python manage.py createsuperuser
ssh ec2-instance "cd /app && python manage.py createsuperuser"
```

**Why?**
- Not automated
- Not reproducible
- Not auditable
- Doesn't work with autoscaling
- Security risk (requires shell access)
- Configuration drift

---

## ✅ Production Approaches

### 1. **Entrypoint Script with Environment Variables** (IMPLEMENTED)

**How it works:**
1. Docker entrypoint script runs on container startup
2. Checks for `DJANGO_SUPERUSER_*` environment variables
3. Automatically creates superuser if variables are set
4. Idempotent - safe to run multiple times

**Files:**
- `docker-entrypoint.sh` - Initialization script
- `Dockerfile` - Uses entrypoint
- `k8s/base/secret.yaml` - Defines superuser variables
- `k8s/overlays/*/secret-patch.yaml` - Environment-specific values

**Entrypoint Script Flow:**
```
Container Starts
    ↓
Wait for Database
    ↓
Run Migrations
    ↓
Create Superuser (if env vars set)
    ↓
Start Application
```

**Environment Variables:**
```bash
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_PASSWORD=secure_password_here
DJANGO_SUPERUSER_EMAIL=admin@example.com
```

**Kubernetes Secret:**
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: connectivity-secrets
stringData:
  DJANGO_SUPERUSER_USERNAME: "admin"
  DJANGO_SUPERUSER_PASSWORD: "your-secure-password"
  DJANGO_SUPERUSER_EMAIL: "admin@yourcompany.com"
```

---

### 2. **Init Container** (Alternative for Kubernetes)

Create a separate init container that runs setup tasks:

```yaml
initContainers:
  - name: django-init
    image: your-app:latest
    command: ["/bin/sh", "-c"]
    args:
      - |
        python manage.py migrate
        python manage.py createsuperuser --noinput || true
    envFrom:
      - secretRef:
          name: connectivity-secrets
```

---

### 3. **Django Management Command** (Custom)

Create a custom management command for initial setup:

```python
# apps/core/management/commands/init_production.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Initialize production environment'

    def handle(self, *args, **options):
        User = get_user_model()
        username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
        
        if not User.objects.filter(username=username).exists():
            User.objects.create_superuser(
                username=username,
                email=os.environ.get('DJANGO_SUPERUSER_EMAIL'),
                password=os.environ.get('DJANGO_SUPERUSER_PASSWORD')
            )
            self.stdout.write(self.style.SUCCESS('Superuser created'))
```

---

### 4. **Configuration Management** (Ansible/Terraform)

For bare metal or VM deployments:

```yaml
# ansible/playbook.yml
- name: Create Django superuser
  command: >
    docker exec app
    python manage.py shell -c
    "from django.contrib.auth.models import User;
    User.objects.create_superuser('{{ admin_user }}', '{{ admin_email }}', '{{ admin_password }}')"
  when: not superuser_exists.stdout
```

---

## 🔐 Security Best Practices

### 1. **Never Commit Secrets**
```bash
# .gitignore
*.secret
secret*.yaml
!secret.yaml.example
```

### 2. **Use Secret Management**

**AWS Secrets Manager:**
```python
import boto3

def get_secret(secret_name):
    client = boto3.client('secretsmanager', region_name='us-east-1')
    response = client.get_secret_value(SecretId=secret_name)
    return response['SecretString']

DJANGO_SUPERUSER_PASSWORD = get_secret('django/admin/password')
```

**HashiCorp Vault:**
```python
import hvac

client = hvac.Client(url='https://vault.example.com')
client.token = os.environ['VAULT_TOKEN']
secret = client.secrets.kv.v2.read_secret_version(path='django/admin')
DJANGO_SUPERUSER_PASSWORD = secret['data']['data']['password']
```

**Kubernetes External Secrets:**
```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: django-admin-credentials
spec:
  secretStoreRef:
    name: aws-secrets-manager
  target:
    name: connectivity-secrets
  data:
    - secretKey: DJANGO_SUPERUSER_PASSWORD
      remoteRef:
        key: prod/django/admin
        property: password
```

### 3. **Kubernetes Sealed Secrets**
```bash
# Create sealed secret
kubectl create secret generic connectivity-secrets \
  --from-literal=DJANGO_SUPERUSER_USERNAME=admin \
  --from-literal=DJANGO_SUPERUSER_PASSWORD=your-password \
  --dry-run=client -o yaml | \
kubeseal --format yaml > sealed-secret.yaml

# Apply sealed secret (safe to commit to git)
kubectl apply -f sealed-secret.yaml
```

---

## 📋 Implementation Checklist

### Development/Local
- ✅ Use `docker-entrypoint.sh` with env vars
- ✅ Store credentials in `k8s/overlays/local/secret-patch.yaml`
- ✅ Simple passwords OK (admin/admin123)

### Staging
- ✅ Use entrypoint script
- ✅ Store credentials in CI/CD secrets (GitHub Secrets)
- ✅ Use moderate password complexity
- ✅ Different credentials than prod

### Production
- ✅ Use entrypoint script
- ✅ Store credentials in AWS Secrets Manager / Vault
- ✅ Strong passwords (16+ chars, random)
- ✅ Rotate passwords quarterly
- ✅ Use Sealed Secrets or External Secrets Operator
- ✅ Enable audit logging
- ✅ Use 2FA for admin accounts (if supported)

---

## 🚀 Deployment Workflow

### Local/Development
```bash
# 1. Set secrets in local overlay
vim k8s/overlays/local/secret-patch.yaml

# 2. Deploy
kubectl apply -k k8s/overlays/local

# 3. Check logs to verify superuser creation
kubectl logs -n connectivity-local deployment/connectivity-service-local | grep superuser
```

### CI/CD (GitHub Actions)
```yaml
# .github/workflows/cd.yml
- name: Deploy to Production
  env:
    DJANGO_SUPERUSER_USERNAME: ${{ secrets.ADMIN_USERNAME }}
    DJANGO_SUPERUSER_PASSWORD: ${{ secrets.ADMIN_PASSWORD }}
    DJANGO_SUPERUSER_EMAIL: ${{ secrets.ADMIN_EMAIL }}
  run: |
    # Create secret
    kubectl create secret generic connectivity-secrets \
      --from-literal=DJANGO_SUPERUSER_USERNAME="$DJANGO_SUPERUSER_USERNAME" \
      --from-literal=DJANGO_SUPERUSER_PASSWORD="$DJANGO_SUPERUSER_PASSWORD" \
      --from-literal=DJANGO_SUPERUSER_EMAIL="$DJANGO_SUPERUSER_EMAIL" \
      --dry-run=client -o yaml | kubectl apply -f -
    
    # Deploy app
    kubectl apply -k k8s/overlays/production
```

### AWS ECS/Fargate
```json
{
  "containerDefinitions": [{
    "secrets": [
      {
        "name": "DJANGO_SUPERUSER_USERNAME",
        "valueFrom": "arn:aws:secretsmanager:region:account:secret:django/admin/username"
      },
      {
        "name": "DJANGO_SUPERUSER_PASSWORD",
        "valueFrom": "arn:aws:secretsmanager:region:account:secret:django/admin/password"
      }
    ]
  }]
}
```

---

## 🧪 Testing Superuser Creation

### Verify in Logs
```bash
kubectl logs -n connectivity-local deployment/connectivity-service-local --tail=50 | grep -i "superuser\|Creating\|admin"
```

### Test Login
```bash
# Get JWT token
curl -X POST http://localhost:8000/api/v1/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# Should return:
# {"access": "eyJ...", "refresh": "eyJ..."}
```

### Exec into Pod (for debugging only)
```bash
kubectl exec -it -n connectivity-local deployment/connectivity-service-local -- \
  python manage.py shell -c "from django.contrib.auth.models import User; print(User.objects.filter(is_superuser=True).values_list('username', flat=True))"
```

---

## 🔄 Password Rotation

### 1. Update Secret
```bash
# Update Kubernetes secret
kubectl edit secret connectivity-secrets -n connectivity

# Or use kubectl patch
kubectl patch secret connectivity-secrets -n connectivity \
  -p '{"stringData":{"DJANGO_SUPERUSER_PASSWORD":"new-password-here"}}'
```

### 2. Update User in Database
```bash
kubectl exec -it deployment/connectivity-service-local -n connectivity -- \
  python manage.py shell -c "
from django.contrib.auth.models import User
user = User.objects.get(username='admin')
user.set_password('new-password-here')
user.save()
print('Password updated')
"
```

### 3. Restart Pods (if needed)
```bash
kubectl rollout restart deployment/connectivity-service-local -n connectivity
```

---

## 📊 Comparison

| Approach | Automation | Security | Complexity | Best For |
|----------|-----------|----------|------------|----------|
| **Entrypoint + Env Vars** | ✅ High | ⭐⭐⭐ | Low | Docker/K8s (All) |
| **Init Container** | ✅ High | ⭐⭐⭐ | Medium | Kubernetes |
| **External Secrets** | ✅ High | ⭐⭐⭐⭐⭐ | High | Enterprise Prod |
| **Sealed Secrets** | ✅ High | ⭐⭐⭐⭐ | Medium | GitOps |
| **Manual Creation** | ❌ None | ⭐ | Very Low | Never! |

---

## 🎯 Current Implementation

**Status:** ✅ Implemented Entrypoint + Environment Variables approach

**What's Configured:**
- `docker-entrypoint.sh` - Auto-creates superuser on startup
- `Dockerfile` - Uses entrypoint
- `k8s/base/secret.yaml` - Defines required env vars
- `k8s/overlays/local/secret-patch.yaml` - Local credentials set

**Local Credentials:**
- Username: `admin`
- Password: `admin123`
- Email: `admin@connectivity.local`

**Next Steps for Production:**
1. Store credentials in GitHub Secrets
2. Update CD pipeline to inject secrets
3. Consider migrating to AWS Secrets Manager
4. Enable password rotation schedule
5. Implement audit logging for admin actions
