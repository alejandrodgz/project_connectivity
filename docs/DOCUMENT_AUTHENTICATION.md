# Document Authentication Service

## Overview

The document authentication service is an **event-driven** microservice that:
1. Listens to RabbitMQ events for document authentication requests
2. Calls an external API to authenticate documents
3. Publishes result events back to RabbitMQ

## Architecture

```
┌─────────────────┐       ┌──────────────────┐       ┌─────────────────┐
│  External       │──────▶│   RabbitMQ       │──────▶│  Document Auth  │
│  Microservice   │       │   Queue          │       │  Consumer       │
└─────────────────┘       └──────────────────┘       └─────────────────┘
     Publishes                 Routing Key:                   │
     event         document.authentication.requested          │
                                                               ▼
                                                    ┌──────────────────────┐
                                                    │  Call External API   │
                                                    │  PUT /apis/          │
                                                    │  authenticateDocument│
                                                    └──────────────────────┘
                                                               │
                                                               ▼
                                                    ┌──────────────────────┐
                                                    │  Save to Database    │
                                                    │  (audit trail)       │
                                                    └──────────────────────┘
                                                               │
                                                               ▼
                                                    ┌──────────────────────┐
                                                    │  Publish Result      │
                                                    │  Event to RabbitMQ   │
                                                    └──────────────────────┘
                                                               │
                                    ┌──────────────────────────┴──────────────────────────┐
                                    ▼                                                     ▼
                         ┌─────────────────────┐                           ┌─────────────────────┐
                         │  Routing Key:       │                           │  Routing Key:       │
                         │  document.auth.     │                           │  document.auth.     │
                         │  success            │                           │  failure            │
                         └─────────────────────┘                           └─────────────────────┘
```

## Event Format

### Input Event (Consumed)
**Routing Key:** `document.authentication.requested` (configurable)

```json
{
  "idCitizen": 1234567890,
  "UrlDocument": "https://bucket.s3.amazonaws.com/file.jpg?...",
  "documentTitle": "Diploma Grado"
}
```

### Output Events (Published)

#### Success Event
**Routing Key:** `document.authentication.ready`

```json
{
  "idCitizen": 1234567890,
  "UrlDocument": "https://bucket.s3.amazonaws.com/file.jpg?...",
  "documentTitle": "Diploma Grado",
  "authSuccess": true
}
```

#### Failure Event
**Routing Key:** `document.auth.failure`

```json
{
  "idCitizen": 1234567890,
  "UrlDocument": "https://bucket.s3.amazonaws.com/file.jpg?...",
  "documentTitle": "Diploma Grado",
  "authSuccess": false
}
```

## External API Integration

**Endpoint:** `PUT https://govcarpeta-apis-4905ff3c005b.herokuapp.com/apis/authenticateDocument`

**Request Body:**
```json
{
  "idCitizen": 1234567890,
  "UrlDocument": "https://bucket.s3.amazonaws.com/file.jpg?...",
  "documentTitle": "Diploma Grado"
}
```

**Response:**
- **200 OK**: Document authenticated successfully → `authSuccess: true`
- **Other codes**: Authentication failed → `authSuccess: false`

## Configuration

### Environment Variables (.env)

```bash
# RabbitMQ Configuration
RABBITMQ_HOST=rabbitmq
RABBITMQ_PORT=5672
RABBITMQ_USER=admin
RABBITMQ_PASSWORD=admin
RABBITMQ_VHOST=/
RABBITMQ_EXCHANGE=citizen_affiliation

# Queue and Routing Key (customizable)
RABBITMQ_DOCUMENT_AUTH_QUEUE=document.authentication.requested
RABBITMQ_DOCUMENT_AUTH_ROUTING_KEY=document.authentication.requested

# External API
EXTERNAL_AFFILIATION_API_URL=https://govcarpeta-apis-4905ff3c005b.herokuapp.com
EXTERNAL_API_TIMEOUT=30
```

## Starting the Consumer

### Using Docker Compose

```bash
docker-compose exec web python manage.py consume_document_auth
```

### With Custom Routing Key

```bash
docker-compose exec web python manage.py consume_document_auth --routing-key document.auth.request
```

### Output

```
======================================================================
DOCUMENT AUTHENTICATION CONSUMER
======================================================================

Listening to routing key: document.authentication.requested
Exchange: citizen_affiliation

Press CTRL+C to stop

======================================================================

📄 Processing document for citizen 1234567890: Diploma Grado
✅ Authentication successful for citizen 1234567890
```

## Database Model

All authentication attempts are saved for audit purposes:

```python
class DocumentAuthentication(models.Model):
    # Document info
    id_citizen = BigIntegerField
    url_document = URLField
    document_title = CharField
    
    # Result
    status = CharField  # PENDING, SUCCESS, FAILED, ERROR
    auth_success = BooleanField
    
    # External API response
    external_api_status_code = IntegerField
    external_api_response = JSONField
    error_message = TextField
    
    # Timestamps
    received_at = DateTimeField
    processed_at = DateTimeField
    event_published_at = DateTimeField
```

## Workflow

1. **Receive Event**: Consumer listens to `document.authentication.requested` routing key
2. **Validate Message**: Check required fields (`idCitizen`, `UrlDocument`, `documentTitle`)
3. **Create Record**: Save initial record with `status='PENDING'`
4. **Call External API**: PUT to `/apis/authenticateDocument`
5. **Update Record**: 
   - If 200: `status='SUCCESS'`, `auth_success=True`
   - Otherwise: `status='FAILED'`, `auth_success=False`
6. **Publish Result**: 
   - Success: Route to `document.authentication.ready`
   - Failure: Route to `document.auth.failure`

## Testing

### Publish Test Event

```bash
docker-compose exec rabbitmq rabbitmqadmin publish \
  exchange=citizen_affiliation \
  routing_key=document.authentication.requested \
  payload='{"idCitizen": 1234567890, "UrlDocument": "https://example.com/doc.pdf", "documentTitle": "Test Document"}'
```

### Check Database

```bash
docker-compose exec web python manage.py shell
```

```python
from apps.documents.models import DocumentAuthentication

# List all authentications
for doc in DocumentAuthentication.objects.all():
    print(f"{doc.id_citizen} - {doc.document_title} - {doc.status} - {doc.auth_success}")
```

## Monitoring

### Logs

```bash
# Follow consumer logs
docker-compose logs -f web | grep "document"
```

### RabbitMQ Management UI

```
http://localhost:15672
Username: admin
Password: admin
```

Check queues:
- `document.authentication.requested` - Input queue
- `document.authentication.ready` - Success output queue
- Monitor message rates and processing

## Production Deployment

### Supervisor/Systemd Service

Create a service to keep the consumer running:

```ini
[program:document_auth_consumer]
command=/path/to/venv/bin/python manage.py consume_document_auth
directory=/path/to/project
autostart=true
autorestart=true
stderr_logfile=/var/log/document_auth_consumer.err.log
stdout_logfile=/var/log/document_auth_consumer.out.log
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: document-auth-consumer
spec:
  replicas: 2  # Multiple consumers for load balancing
  selector:
    matchLabels:
      app: document-auth-consumer
  template:
    metadata:
      labels:
        app: document-auth-consumer
    spec:
      containers:
      - name: consumer
        image: your-image:latest
        command: ["python", "manage.py", "consume_document_auth"]
        env:
        - name: RABBITMQ_HOST
          value: "rabbitmq-service"
        - name: RABBITMQ_USER
          valueFrom:
            secretKeyRef:
              name: rabbitmq-secret
              key: username
        - name: RABBITMQ_PASSWORD
          valueFrom:
            secretKeyRef:
              name: rabbitmq-secret
              key: password
```

## Error Handling

### Retry Logic

The consumer uses RabbitMQ's built-in retry mechanism:
- Failed messages are requeued
- External API client has 3 retry attempts with exponential backoff

### Dead Letter Queue (Optional)

Configure a DLQ for messages that fail repeatedly:

```python
# In consumer.py, add:
self.channel.queue_declare(
    queue=self.queue_name,
    durable=True,
    arguments={
        'x-dead-letter-exchange': 'citizen_affiliation_dlx',
        'x-message-ttl': 86400000  # 24 hours
    }
)
```

## Troubleshooting

### Consumer not receiving messages

1. Check RabbitMQ connection:
```bash
docker-compose exec web python manage.py shell -c "from infrastructure.rabbitmq.consumer import *; print('OK')"
```

2. Verify queue binding:
```bash
docker-compose exec rabbitmq rabbitmqctl list_bindings
```

3. Check routing key matches

### External API errors

1. Check API URL in .env
2. Verify network connectivity
3. Check API logs/response in database:

```python
from apps.documents.models import DocumentAuthentication
failed = DocumentAuthentication.objects.filter(status='FAILED').last()
print(failed.error_message)
print(failed.external_api_response)
```

## Next Steps

- [ ] Add unit tests for document service
- [ ] Add integration tests with RabbitMQ
- [ ] Implement metrics/monitoring (Prometheus)
- [ ] Add rate limiting for external API calls
- [ ] Configure DLQ for failed messages
- [ ] Add alerting for repeated failures
