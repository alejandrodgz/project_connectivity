# Quick Reference Guide

## For Administrators

### Create Service Account
```bash
docker-compose exec web python manage.py create_service_account <service-name>
```

### List Service Accounts
```bash
docker-compose exec web python manage.py shell -c "
from django.contrib.auth.models import User
for u in User.objects.filter(is_staff=False): print(f'{u.username} - Active: {u.is_active}')
"
```

### Deactivate Account
```bash
docker-compose exec web python manage.py shell -c "
from django.contrib.auth.models import User
User.objects.filter(username='SERVICE_NAME').update(is_active=False)
"
```

---

## For External Services

### 1. Get Token
```bash
curl -X POST https://api.example.com/api/v1/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "your-service", "password": "your-password"}'
```

### 2. Check Affiliation
```bash
curl -X POST https://api.example.com/api/v1/affiliation/check/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"citizen_id": "1128456232"}'
```

### 3. Refresh Token
```bash
curl -X POST https://api.example.com/api/v1/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{"refresh": "YOUR_REFRESH_TOKEN"}'
```

---

## Response Codes

| Code | Meaning |
|------|---------|
| 200  | ✅ CAN create affiliation |
| 204  | ❌ CANNOT create affiliation |
| 400  | Invalid request |
| 401  | Unauthorized (bad/expired token) |
| 500  | Server error |

---

## Token Lifetimes

- **Access Token**: 15 minutes
- **Refresh Token**: 7 days

**Recommendation**: Refresh access token every 14 minutes

---

## Documentation

- **External Service Integration**: `docs/EXTERNAL_SERVICE_INTEGRATION.md`
- **Administrator Guide**: `docs/ADMIN_GUIDE.md`
- **API Documentation**: `http://localhost:8000/api/docs/`
