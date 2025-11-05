# Quick Start Guide

## Prerequisites
- Docker and Docker Compose installed
- Python 3.12 with venv already created at `/home/alejo/connectivity/project_connectivity/venv/`

## 🚀 Getting Started

### 1. Set Up Environment Variables
```bash
cd /home/alejo/connectivity/project_connectivity

# Copy the example env file
cp .env.example .env

# Edit .env with your configuration (or use defaults for development)
nano .env
```

### 2. Start Services with Docker Compose
```bash
# Start MariaDB, Redis, RabbitMQ, Prometheus, and Grafana
docker-compose up -d db redis rabbitmq prometheus grafana

# Wait for services to be ready (about 30 seconds)
docker-compose ps
```

### 3. Run Database Migrations
```bash
# Activate virtual environment
source venv/bin/activate

# Apply migrations
python manage.py migrate

# Create a superuser for admin access
python manage.py createsuperuser
```

### 4. Run the Development Server
```bash
# Still in the virtual environment
python manage.py runserver 0.0.0.0:8000
```

The API will be available at:
- **API**: http://localhost:8000/api/v1/
- **Admin**: http://localhost:8000/admin/
- **API Docs**: http://localhost:8000/api/docs/
- **Health Check**: http://localhost:8000/health/

---

## 📊 Service Endpoints

### External Services (Docker Compose)
- **RabbitMQ Management**: http://localhost:15672 (guest/guest)
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)

---

## 🧪 Testing the Affiliation Endpoint

### Step 1: Get a JWT Token

First, create a user via Django admin or shell:
```bash
python manage.py createsuperuser
# Username: admin
# Email: admin@example.com
# Password: admin123
```

Then get a token (you'll need to implement the authentication endpoints, or use the admin user directly):

```bash
# For now, you can create a token programmatically in the Django shell
python manage.py shell

# In the shell:
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken

user = User.objects.get(username='admin')
refresh = RefreshToken.for_user(user)
print(f"Access Token: {refresh.access_token}")
```

### Step 2: Test the Affiliation Check Endpoint

```bash
# Replace YOUR_JWT_TOKEN with the actual token
curl -X POST http://localhost:8000/api/v1/affiliation/check/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "citizen_id": "1128456232"
  }'
```

**Expected Response (Citizen Found):**
```json
{
  "id": 1,
  "citizen_id": "1128456232",
  "status": "ELIGIBLE",
  "exists_in_system": true,
  "is_eligible": true,
  "citizen_data": {
    "name": "...",
    "document_number": "1128456232"
  },
  "message": "Citizen found successfully",
  "checked_at": "2025-10-31T20:00:00.000Z",
  "external_api_status_code": 200
}
```

**Expected Response (Citizen Not Found):**
```json
{
  "id": 2,
  "citizen_id": "9999999999",
  "status": "NOT_FOUND",
  "exists_in_system": false,
  "is_eligible": false,
  "citizen_data": null,
  "message": "Citizen does not exist in the system",
  "checked_at": "2025-10-31T20:00:00.000Z",
  "external_api_status_code": 204
}
```

---

## 🧪 Running Tests

```bash
# Activate virtual environment
source venv/bin/activate

# Run all tests
python manage.py test

# Run only affiliation tests
python manage.py test apps.affiliation.tests

# Run with verbose output
python manage.py test apps.affiliation.tests -v 2

# Run with coverage
pytest --cov=apps.affiliation --cov-report=html
```

---

## 🐰 Verifying RabbitMQ Events

### Via RabbitMQ Management UI:
1. Go to http://localhost:15672
2. Login: guest/guest
3. Click "Exchanges" → Find `citizen_affiliation`
4. Click "Queues" to see if events are being published

### Programmatically (Consumer):
```python
import pika
import json

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='localhost', port=5672)
)
channel = connection.channel()

# Declare exchange
channel.exchange_declare(exchange='citizen_affiliation', exchange_type='topic', durable=True)

# Create a queue and bind it
result = channel.queue_declare(queue='', exclusive=True)
queue_name = result.method.queue
channel.queue_bind(exchange='citizen_affiliation', queue=queue_name, routing_key='affiliation.checked')

def callback(ch, method, properties, body):
    event = json.loads(body)
    print(f"Received event: {event}")

channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
print('Waiting for messages...')
channel.start_consuming()
```

---

## 🔍 Checking Logs

### Application Logs
The application logs to:
- Console (stdout)
- File: `logs/django.log`
- File: `logs/django_debug.log`

```bash
# Tail the logs
tail -f logs/django.log

# Search for specific citizen checks
grep "1128456232" logs/django.log
```

### Docker Logs
```bash
# Django app
docker-compose logs -f web

# RabbitMQ
docker-compose logs -f rabbitmq

# MariaDB
docker-compose logs -f db
```

---

## 🛑 Stopping Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (WARNING: deletes database data)
docker-compose down -v
```

---

## 🚨 Troubleshooting

### Issue: Cannot connect to database
```bash
# Check if MariaDB is running
docker-compose ps db

# Check MariaDB logs
docker-compose logs db

# Verify DATABASE_URL in .env
cat .env | grep DATABASE_URL
```

### Issue: RabbitMQ connection refused
```bash
# Check if RabbitMQ is running
docker-compose ps rabbitmq

# Restart RabbitMQ
docker-compose restart rabbitmq

# Check RabbitMQ logs
docker-compose logs rabbitmq
```

### Issue: External API timeout
```bash
# Test the external API directly
curl https://govcarpeta-apis-4905ff3c005b.herokuapp.com/apis/validateCitizen/1128456232

# Check if EXTERNAL_AFFILIATION_API_URL is set correctly
cat .env | grep EXTERNAL_AFFILIATION_API_URL
```

---

## 📚 Next Steps

1. ✅ Affiliation check is working
2. ⏳ Implement authentication endpoints (JWT login/refresh)
3. ⏳ Implement document authentication functionality
4. ⏳ Set up CI/CD pipeline
5. ⏳ Create Kubernetes manifests
6. ⏳ Add integration tests

---

**Happy Testing! 🎉**
