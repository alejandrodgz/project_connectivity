# Service-to-Service Authentication Guide

## Overview

This service uses **JWT (JSON Web Token) authentication** for external services to consume the API. There are two types of accounts:

| Account Type | Purpose | Created By | Used By |
|--------------|---------|------------|---------|
| **Admin User** | System administration, manual testing | Entrypoint (superuser) | Developers, Ops team |
| **Service Accounts** | Automated API consumption | Entrypoint (service accounts) | External microservices |

---

## Service Accounts

### Configured Services

1. **Document Service** (`document-service`)
   - Consumes: `/api/v1/documents/*` endpoints
   - Publishes: Document authentication events to RabbitMQ

2. **Auth Service** (`auth-service`)
   - Consumes: `/api/v1/affiliation/*` endpoints
   - Purpose: Validate citizen affiliation before authentication

### How Service Accounts Work

```
External Service                    Connectivity Service
(document-service)                  (This API)
      │                                   │
      │  1. POST /api/v1/token/           │
      │     {username, password}          │
      ├──────────────────────────────────>│
      │                                   │
      │  2. Return JWT tokens             │
      │<──────────────────────────────────┤
      │     {access, refresh}             │
      │                                   │
      │  3. GET /api/v1/affiliation/      │
      │     Authorization: Bearer <JWT>   │
      ├──────────────────────────────────>│
      │                                   │
      │  4. Return data                   │
      │<──────────────────────────────────┤
      │     {citizen_data}                │
```

---

## Configuration

### Environment Variables

Add these to your Kubernetes secrets:

```yaml
# Document Service Account
DOCUMENT_SERVICE_USERNAME: "document-service"
DOCUMENT_SERVICE_PASSWORD: "your-secure-password-here"
DOCUMENT_SERVICE_EMAIL: "document-service@yourcompany.com"

# Auth Service Account  
AUTH_SERVICE_USERNAME: "auth-service"
AUTH_SERVICE_PASSWORD: "your-secure-password-here"
AUTH_SERVICE_EMAIL: "auth-service@yourcompany.com"
```

### Local Development

**Credentials (already configured):**
- Document Service: `document-service` / `doc-service-pass-123`
- Auth Service: `auth-service` / `auth-service-pass-123`

### Production

**Store in AWS Secrets Manager:**
```json
{
  "document-service": {
    "username": "document-service-prod",
    "password": "STRONG-RANDOM-PASSWORD-HERE",
    "email": "document-service@prod.yourcompany.com"
  },
  "auth-service": {
    "username": "auth-service-prod",
    "password": "STRONG-RANDOM-PASSWORD-HERE",
    "email": "auth-service@prod.yourcompany.com"
  }
}
```

---

## Usage Examples

### 1. Getting JWT Token

External services must first obtain a JWT token:

```bash
# Request
curl -X POST http://connectivity-service/api/v1/token/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "document-service",
    "password": "doc-service-pass-123"
  }'

# Response
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### 2. Using JWT Token

Use the `access` token in the `Authorization` header:

```bash
curl -X POST http://connectivity-service/api/v1/affiliation/check/ \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "citizen_id": "1128456232"
  }'
```

### 3. Refreshing Token

When the access token expires (default: 15 minutes), use the refresh token:

```bash
curl -X POST http://connectivity-service/api/v1/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{
    "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }'
```

---

## Client Implementation Examples

### Python (for External Services)

```python
import requests
from datetime import datetime, timedelta

class ConnectivityServiceClient:
    def __init__(self, base_url, username, password):
        self.base_url = base_url
        self.username = username
        self.password = password
        self.access_token = None
        self.refresh_token = None
        self.token_expiry = None
    
    def _get_token(self):
        """Obtain JWT token."""
        response = requests.post(
            f"{self.base_url}/api/v1/token/",
            json={"username": self.username, "password": self.password}
        )
        response.raise_for_status()
        data = response.json()
        
        self.access_token = data['access']
        self.refresh_token = data['refresh']
        # Tokens expire in 15 minutes
        self.token_expiry = datetime.now() + timedelta(minutes=14)
    
    def _refresh_token_if_needed(self):
        """Refresh token if expired."""
        if not self.access_token or datetime.now() >= self.token_expiry:
            if self.refresh_token:
                try:
                    response = requests.post(
                        f"{self.base_url}/api/v1/token/refresh/",
                        json={"refresh": self.refresh_token}
                    )
                    response.raise_for_status()
                    data = response.json()
                    self.access_token = data['access']
                    self.token_expiry = datetime.now() + timedelta(minutes=14)
                except:
                    # Refresh failed, get new token
                    self._get_token()
            else:
                self._get_token()
    
    def _make_request(self, method, endpoint, **kwargs):
        """Make authenticated request."""
        self._refresh_token_if_needed()
        
        headers = kwargs.pop('headers', {})
        headers['Authorization'] = f'Bearer {self.access_token}'
        
        response = requests.request(
            method,
            f"{self.base_url}{endpoint}",
            headers=headers,
            **kwargs
        )
        return response
    
    def check_affiliation(self, citizen_id):
        """Check citizen affiliation eligibility."""
        response = self._make_request(
            'POST',
            '/api/v1/affiliation/check/',
            json={'citizen_id': citizen_id}
        )
        response.raise_for_status()
        return response.json()


# Usage in Document Service
client = ConnectivityServiceClient(
    base_url='http://connectivity-service',
    username='document-service',
    password='doc-service-pass-123'
)

# Call the API
result = client.check_affiliation('1128456232')
print(result)
```

### Node.js (for External Services)

```javascript
const axios = require('axios');

class ConnectivityServiceClient {
  constructor(baseURL, username, password) {
    this.baseURL = baseURL;
    this.username = username;
    this.password = password;
    this.accessToken = null;
    this.refreshToken = null;
    this.tokenExpiry = null;
  }

  async getToken() {
    const response = await axios.post(`${this.baseURL}/api/v1/token/`, {
      username: this.username,
      password: this.password
    });
    
    this.accessToken = response.data.access;
    this.refreshToken = response.data.refresh;
    this.tokenExpiry = Date.now() + (14 * 60 * 1000); // 14 minutes
  }

  async refreshTokenIfNeeded() {
    if (!this.accessToken || Date.now() >= this.tokenExpiry) {
      if (this.refreshToken) {
        try {
          const response = await axios.post(`${this.baseURL}/api/v1/token/refresh/`, {
            refresh: this.refreshToken
          });
          this.accessToken = response.data.access;
          this.tokenExpiry = Date.now() + (14 * 60 * 1000);
        } catch (error) {
          await this.getToken();
        }
      } else {
        await this.getToken();
      }
    }
  }

  async checkAffiliation(citizenId) {
    await this.refreshTokenIfNeeded();
    
    const response = await axios.post(
      `${this.baseURL}/api/v1/affiliation/check/`,
      { citizen_id: citizenId },
      {
        headers: {
          'Authorization': `Bearer ${this.accessToken}`
        }
      }
    );
    
    return response.data;
  }
}

// Usage
const client = new ConnectivityServiceClient(
  'http://connectivity-service',
  'document-service',
  'doc-service-pass-123'
);

const result = await client.checkAffiliation('1128456232');
console.log(result);
```

---

## Security Best Practices

### 1. **Separate Credentials per Environment**

```yaml
# Development
DOCUMENT_SERVICE_PASSWORD: "simple-dev-password"

# Staging  
DOCUMENT_SERVICE_PASSWORD: "moderate-staging-password-123"

# Production
DOCUMENT_SERVICE_PASSWORD: "Xy9$mK2pL#vR8nQ!wE5tA" # Strong random
```

### 2. **Rotate Service Account Passwords**

```bash
# Update password in secrets
kubectl edit secret connectivity-secrets -n connectivity

# Update password in database
kubectl exec -it deployment/connectivity-service -n connectivity -- \
  python manage.py shell -c "
from django.contrib.auth.models import User
user = User.objects.get(username='document-service')
user.set_password('NEW-PASSWORD-HERE')
user.save()
"

# Restart to pick up new credentials
kubectl rollout restart deployment/connectivity-service -n connectivity
```

### 3. **Use Secret Management**

**AWS Secrets Manager:**
```python
import boto3
import json

def get_service_credentials(service_name):
    client = boto3.client('secretsmanager', region_name='us-east-1')
    response = client.get_secret_value(SecretId=f'connectivity/{service_name}')
    return json.loads(response['SecretString'])

# In document-service
credentials = get_service_credentials('document-service')
client = ConnectivityServiceClient(
    base_url=CONNECTIVITY_URL,
    username=credentials['username'],
    password=credentials['password']
)
```

### 4. **Limit Token Lifetime**

Edit `settings.py` for stricter security:

```python
# For service accounts, use shorter access tokens
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=5),  # Shorter
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),   # Longer refresh
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}
```

### 5. **Monitor Service Account Usage**

```python
# Add logging middleware
class ServiceAccountAuditMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        if request.user.is_authenticated:
            if request.user.groups.filter(name='service_accounts').exists():
                logger.info(
                    f"Service account access: {request.user.username} "
                    f"called {request.path} from {request.META.get('REMOTE_ADDR')}"
                )
        return self.get_response(request)
```

---

## Testing

### Manual Test with curl

```bash
# 1. Get token
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"document-service","password":"doc-service-pass-123"}' \
  | jq -r '.access')

# 2. Call API
curl -X POST http://localhost:8000/api/v1/affiliation/check/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"citizen_id":"1128456232"}'
```

### Automated Test

```python
import pytest
from myapp.clients import ConnectivityServiceClient

def test_document_service_authentication():
    client = ConnectivityServiceClient(
        base_url='http://connectivity-service:8000',
        username='document-service',
        password='doc-service-pass-123'
    )
    
    # Should successfully authenticate
    result = client.check_affiliation('1128456232')
    assert 'is_eligible' in result
```

---

## Troubleshooting

### "Invalid credentials" Error

```bash
# Check if service account exists
kubectl exec -it deployment/connectivity-service -n connectivity -- \
  python manage.py shell -c "
from django.contrib.auth.models import User
print(User.objects.filter(username='document-service').exists())
"

# Verify password
kubectl exec -it deployment/connectivity-service -n connectivity -- \
  python manage.py shell -c "
from django.contrib.auth.models import User
user = User.objects.get(username='document-service')
print(user.check_password('doc-service-pass-123'))
"
```

### "Token expired" Error

- Access tokens expire after 15 minutes (configurable)
- Use refresh token to get new access token
- Implement automatic token refresh in client

### Check Service Account in DB

```bash
kubectl exec -it deployment/connectivity-service -n connectivity -- \
  python manage.py shell -c "
from django.contrib.auth.models import User
users = User.objects.filter(groups__name='service_accounts')
for user in users:
    print(f'{user.username} - {user.email} - Active: {user.is_active}')
"
```

---

## Summary

✅ **Admin User**: Created by `DJANGO_SUPERUSER_*` env vars (for you)
✅ **Service Accounts**: Created by `*_SERVICE_*` env vars (for external services)

Both are **automatically created** on container startup via the entrypoint script. No manual intervention needed!
