# External Service Integration Guide

## Overview

This document provides instructions for external services to integrate with the Citizen Affiliation Microservice.

## Authentication

The API uses JWT (JSON Web Tokens) for authentication.

### Step 1: Obtain Credentials

Contact the administrator to create a service account. You will receive:
- **Username**: `your-service-name`
- **Password**: `SecurePassword123`
- **Base URL**: `https://affiliation-api.example.com`

### Step 2: Obtain JWT Token

**Endpoint:** `POST /api/v1/token/`

```bash
curl -X POST https://affiliation-api.example.com/api/v1/token/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "your-service-name",
    "password": "SecurePassword123"
  }'
```

**Response:**
```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

- `access`: Use for API requests (expires in 15 minutes)
- `refresh`: Use to obtain new access token (expires in 7 days)

### Step 3: Use Access Token

Include the access token in the `Authorization` header:

```bash
curl -X POST https://affiliation-api.example.com/api/v1/affiliation/check/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "citizen_id": "1128456232"
  }'
```

### Step 4: Refresh Token (When Access Token Expires)

**Endpoint:** `POST /api/v1/token/refresh/`

```bash
curl -X POST https://affiliation-api.example.com/api/v1/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{
    "refresh": "YOUR_REFRESH_TOKEN"
  }'
```

**Response:**
```json
{
  "access": "NEW_ACCESS_TOKEN"
}
```

## API Endpoints

### Check Affiliation Eligibility

**Endpoint:** `POST /api/v1/affiliation/check/`

**Request:**
```json
{
  "citizen_id": "1128456232"
}
```

**Response (HTTP 200 - CAN Create Affiliation):**
```json
{
  "citizen_id": "1128456232",
  "is_eligible": true,
  "external_api_status_code": 204,
  "citizen_data": null
}
```

**Response (HTTP 204 - CANNOT Create Affiliation):**
```json
{
  "citizen_id": "8888888888",
  "is_eligible": false,
  "external_api_status_code": 200,
  "citizen_data": "El ciudadano con id: 8888888888 se encuentra registrado..."
}
```

## Implementation Examples

### Python Example

```python
import requests
from datetime import datetime, timedelta

class AffiliationServiceClient:
    def __init__(self, base_url, username, password):
        self.base_url = base_url
        self.username = username
        self.password = password
        self.access_token = None
        self.refresh_token = None
        self.token_expiry = None
    
    def authenticate(self):
        """Obtain JWT tokens"""
        response = requests.post(
            f'{self.base_url}/api/v1/token/',
            json={'username': self.username, 'password': self.password}
        )
        response.raise_for_status()
        data = response.json()
        
        self.access_token = data['access']
        self.refresh_token = data['refresh']
        self.token_expiry = datetime.now() + timedelta(minutes=14)
    
    def refresh_token_if_needed(self):
        """Refresh access token if expired"""
        if not self.access_token or datetime.now() >= self.token_expiry:
            if self.refresh_token:
                response = requests.post(
                    f'{self.base_url}/api/v1/token/refresh/',
                    json={'refresh': self.refresh_token}
                )
                if response.status_code == 200:
                    self.access_token = response.json()['access']
                    self.token_expiry = datetime.now() + timedelta(minutes=14)
                else:
                    self.authenticate()
            else:
                self.authenticate()
    
    def check_affiliation(self, citizen_id):
        """Check if citizen can be affiliated"""
        self.refresh_token_if_needed()
        
        response = requests.post(
            f'{self.base_url}/api/v1/affiliation/check/',
            headers={'Authorization': f'Bearer {self.access_token}'},
            json={'citizen_id': citizen_id}
        )
        
        if response.status_code == 200:
            return {'can_affiliate': True, **response.json()}
        elif response.status_code == 204:
            return {'can_affiliate': False, **response.json()}
        else:
            response.raise_for_status()

# Usage
client = AffiliationServiceClient(
    base_url='https://affiliation-api.example.com',
    username='payment-service',
    password='SecurePassword123'
)

# Check affiliation
result = client.check_affiliation('1128456232')
if result['can_affiliate']:
    print("✅ Can create affiliation")
else:
    print(f"❌ Cannot affiliate: {result['citizen_data']}")
```

### Node.js Example

```javascript
const axios = require('axios');

class AffiliationServiceClient {
    constructor(baseUrl, username, password) {
        this.baseUrl = baseUrl;
        this.username = username;
        this.password = password;
        this.accessToken = null;
        this.refreshToken = null;
        this.tokenExpiry = null;
    }

    async authenticate() {
        const response = await axios.post(`${this.baseUrl}/api/v1/token/`, {
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
                    const response = await axios.post(
                        `${this.baseUrl}/api/v1/token/refresh/`,
                        { refresh: this.refreshToken }
                    );
                    this.accessToken = response.data.access;
                    this.tokenExpiry = Date.now() + (14 * 60 * 1000);
                } catch (error) {
                    await this.authenticate();
                }
            } else {
                await this.authenticate();
            }
        }
    }

    async checkAffiliation(citizenId) {
        await this.refreshTokenIfNeeded();
        
        const response = await axios.post(
            `${this.baseUrl}/api/v1/affiliation/check/`,
            { citizen_id: citizenId },
            { headers: { 'Authorization': `Bearer ${this.accessToken}` } }
        );
        
        return {
            can_affiliate: response.status === 200,
            ...response.data
        };
    }
}

// Usage
const client = new AffiliationServiceClient(
    'https://affiliation-api.example.com',
    'payment-service',
    'SecurePassword123'
);

(async () => {
    const result = await client.checkAffiliation('1128456232');
    if (result.can_affiliate) {
        console.log('✅ Can create affiliation');
    } else {
        console.log(`❌ Cannot affiliate: ${result.citizen_data}`);
    }
})();
```

## Error Handling

### HTTP Status Codes

| Status Code | Meaning | Action |
|-------------|---------|--------|
| 200 OK | Citizen CAN be affiliated | Proceed with affiliation |
| 204 No Content | Citizen CANNOT be affiliated | Show error to user |
| 400 Bad Request | Invalid citizen_id format | Fix validation |
| 401 Unauthorized | Invalid/expired token | Refresh or re-authenticate |
| 500 Internal Server Error | Server error | Retry with exponential backoff |

### Example Error Responses

**400 Bad Request:**
```json
{
  "error": "Invalid request data",
  "details": {
    "citizen_id": ["Citizen ID must be between 6 and 12 digits"]
  }
}
```

**401 Unauthorized:**
```json
{
  "detail": "Given token not valid for any token type",
  "code": "token_not_valid"
}
```

## Best Practices

1. **Store Credentials Securely**
   - Use environment variables
   - Never commit credentials to source control
   - Use secret managers (AWS Secrets Manager, Azure Key Vault, etc.)

2. **Token Management**
   - Cache access tokens
   - Refresh before expiration (don't wait for 401)
   - Implement retry logic for token refresh failures

3. **Error Handling**
   - Implement exponential backoff for retries
   - Log all API errors for debugging
   - Handle network timeouts gracefully

4. **Rate Limiting**
   - Respect rate limits (1000 requests/hour for authenticated users)
   - Implement client-side rate limiting if needed

5. **Monitoring**
   - Monitor token refresh failures
   - Track API response times
   - Alert on repeated 401 errors

## Support

For issues or questions, contact:
- Email: api-support@example.com
- Documentation: https://docs.affiliation-api.example.com
