# Administrator Guide: External Service Setup

## Overview

This guide explains how to set up authentication for external services that need to consume the Affiliation Microservice API.

## Process Flow

```
┌─────────────────┐       ┌──────────────────┐       ┌─────────────────┐
│  Administrator  │──────▶│  Create Service  │──────▶│ Share Creds     │
│                 │       │  Account         │       │ Securely        │
└─────────────────┘       └──────────────────┘       └─────────────────┘
                                                              │
                                                              ▼
┌─────────────────┐       ┌──────────────────┐       ┌─────────────────┐
│ External Service│◀──────│  External Service│◀──────│ Receives        │
│ Consumes API    │       │  Implements Auth │       │ Credentials     │
└─────────────────┘       └──────────────────┘       └─────────────────┘
```

## Step 1: Create Service Account

As an administrator, use the management command to create a service account:

```bash
docker-compose exec web python manage.py create_service_account <service-name> [options]
```

### Options:
- `service-name` (required): Name of the external service (e.g., `payment-service`, `document-service`)
- `--password <password>`: Custom password (auto-generated if not provided)
- `--email <email>`: Email address for the service account

### Examples:

**Auto-generate password:**
```bash
docker-compose exec web python manage.py create_service_account payment-service --email tech@payment.com
```

**Custom password:**
```bash
docker-compose exec web python manage.py create_service_account document-service \
  --password "MySecurePassword123!" \
  --email tech@documents.com
```

### Output:

```
======================================================================
SERVICE ACCOUNT CREATED SUCCESSFULLY
======================================================================

Service Name: payment-service
Username:     payment-service
Password:     $WZOG$r3WAMGWQrnurfo#c9*
Email:        tech@payment.com

⚠️  IMPORTANT: Save these credentials securely!
   This is the only time the password will be displayed.

======================================================================

Provide these credentials to the external service:

  Username: payment-service
  Password: $WZOG$r3WAMGWQrnurfo#c9*

  Token Endpoint: POST /api/v1/token/
  Affiliation Endpoint: POST /api/v1/affiliation/check/

======================================================================
```

## Step 2: Share Credentials Securely

**⚠️ SECURITY: Never share credentials via insecure channels!**

### Recommended Methods:
1. **Secret Manager / Vault** (Best)
   - AWS Secrets Manager
   - Azure Key Vault
   - HashiCorp Vault
   - Google Secret Manager

2. **Encrypted Communication**
   - PGP-encrypted email
   - Secure messaging (Signal, etc.)
   - Password-protected documents

3. **In-Person / Video Call**
   - Read credentials over secure video call
   - Share via screen sharing (ensure recording is off)

### Information to Share:

```yaml
Service Account Information:
  Service Name: payment-service
  Username: payment-service
  Password: [GENERATED_PASSWORD]
  Email: tech@payment.com

API Endpoints:
  Base URL: https://affiliation-api.example.com
  Token Obtain: POST /api/v1/token/
  Token Refresh: POST /api/v1/token/refresh/
  Token Verify: POST /api/v1/token/verify/
  Affiliation Check: POST /api/v1/affiliation/check/

Token Configuration:
  Access Token Lifetime: 15 minutes
  Refresh Token Lifetime: 7 days
  
Rate Limits:
  Authenticated Users: 1000 requests/hour

Documentation:
  Integration Guide: [Link to EXTERNAL_SERVICE_INTEGRATION.md]
```

## Step 3: External Service Implementation

The external service should implement:

1. **Initial Authentication**
   - POST to `/api/v1/token/` with username/password
   - Store access and refresh tokens securely

2. **Token Management**
   - Use access token for API requests
   - Refresh token before expiration (14 minutes recommended)
   - Re-authenticate if refresh fails

3. **API Consumption**
   - Include `Authorization: Bearer <token>` header
   - Handle HTTP status codes appropriately

See `docs/EXTERNAL_SERVICE_INTEGRATION.md` for implementation examples.

## Step 4: Monitoring & Maintenance

### View Existing Service Accounts

```bash
docker-compose exec web python manage.py shell
```

```python
from django.contrib.auth.models import User

# List all service accounts
service_accounts = User.objects.filter(is_staff=False, is_superuser=False)
for user in service_accounts:
    print(f"Service: {user.username}, Email: {user.email}, Active: {user.is_active}")
```

### Deactivate Service Account

```python
from django.contrib.auth.models import User

user = User.objects.get(username='payment-service')
user.is_active = False
user.save()
print(f"Service account '{user.username}' has been deactivated")
```

### Reset Password

```python
from django.contrib.auth.models import User

user = User.objects.get(username='payment-service')
new_password = 'NewSecurePassword123!'
user.set_password(new_password)
user.save()
print(f"Password reset for '{user.username}'")
print(f"New password: {new_password}")
```

### Delete Service Account

```python
from django.contrib.auth.models import User

user = User.objects.get(username='payment-service')
username = user.username
user.delete()
print(f"Service account '{username}' has been deleted")
```

## Security Best Practices

### 1. Credential Management
- ✅ Use auto-generated passwords (24+ characters)
- ✅ Store credentials in secret managers
- ✅ Rotate credentials periodically (every 90 days)
- ❌ Never commit credentials to version control
- ❌ Never log credentials

### 2. Access Control
- ✅ Create separate accounts per service
- ✅ Use principle of least privilege
- ✅ Deactivate unused accounts
- ✅ Monitor authentication failures

### 3. Network Security
- ✅ Use HTTPS/TLS in production
- ✅ Implement IP whitelisting (if possible)
- ✅ Use VPN or private networks
- ✅ Enable rate limiting

### 4. Monitoring
- ✅ Log all authentication attempts
- ✅ Alert on repeated failures
- ✅ Monitor token refresh patterns
- ✅ Track API usage per service

## Troubleshooting

### Issue: External service cannot authenticate

**Check:**
1. Verify username/password are correct
2. Ensure account is active: `user.is_active == True`
3. Check network connectivity
4. Verify API endpoint URL

**Solution:**
```bash
docker-compose exec web python manage.py shell
```

```python
from django.contrib.auth.models import User

user = User.objects.get(username='payment-service')
print(f"Active: {user.is_active}")
print(f"Username: {user.username}")

# Reactivate if needed
if not user.is_active:
    user.is_active = True
    user.save()
```

### Issue: Token expired errors

**Cause:** External service not refreshing tokens properly

**Solution:** Contact external service team, provide refresh token documentation

### Issue: Need to revoke access immediately

**Solution:**
```python
from django.contrib.auth.models import User

user = User.objects.get(username='payment-service')
user.is_active = False
user.save()
```

## Production Checklist

Before deploying to production:

- [ ] Enable HTTPS/TLS
- [ ] Configure rate limiting
- [ ] Set up monitoring and alerting
- [ ] Document all service accounts
- [ ] Implement credential rotation policy
- [ ] Set up audit logging
- [ ] Configure IP whitelisting (if applicable)
- [ ] Test token refresh flow
- [ ] Prepare incident response plan

## Support

For questions or issues:
- Technical Documentation: `docs/EXTERNAL_SERVICE_INTEGRATION.md`
- Administrator Email: admin@example.com
- Emergency Contact: +1-xxx-xxx-xxxx
