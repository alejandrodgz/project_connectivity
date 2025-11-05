# Event Naming Changes

## Summary
Updated RabbitMQ event names to be more descriptive and follow a consistent naming pattern.

## Changes Made

### Input Event (Consumed)
- **Old**: `document.authentication`
- **New**: `document.authentication.requested`
- **Rationale**: Makes it clear this is a request/trigger event

### Success Output Event (Published)
- **Old**: `document.auth.success`
- **New**: `document.authentication.ready`
- **Rationale**: More explicit about what state the document is in; aligns with naming pattern

### Failure Output Event (Published)
- **Old**: `document.auth.failure`
- **New**: `document.auth.failure` (unchanged)
- **Note**: Keeping this for now; could be changed to `document.authentication.failed` for consistency

## Files Updated

### Application Code
1. **apps/documents/services.py**
   - Line 130: Changed success routing key to `document.authentication.ready`

2. **infrastructure/rabbitmq/consumer.py**
   - Line 20: Updated default routing_key parameter to `document.authentication.requested`
   - Line 27: Updated docstring
   - Line 46: Updated default fallback value

3. **apps/documents/management/commands/consume_document_auth.py**
   - Line 23: Updated default routing key to `document.authentication.requested`
   - Line 24: Updated help text

### Configuration Files
4. **.env.example**
   - Line 57: `RABBITMQ_DOCUMENT_AUTH_QUEUE=document.authentication.requested`
   - Line 58: `RABBITMQ_DOCUMENT_AUTH_ROUTING_KEY=document.authentication.requested`

5. **settings/settings.py**
   - Line 254: Updated default for `RABBITMQ_DOCUMENT_AUTH_QUEUE`
   - Line 255: Updated default for `RABBITMQ_DOCUMENT_AUTH_ROUTING_KEY`

### Tests
6. **apps/documents/tests.py**
   - Line 145: Updated expected routing key to `document.authentication.ready`
   - Line 240: Updated expected routing key to `document.authentication.ready`

### Documentation
7. **docs/DOCUMENT_AUTHENTICATION.md**
   - Line 17: Updated diagram routing key
   - Line 50: Updated input event routing key
   - Line 63: Updated success event routing key
   - Line 118: Updated configuration example
   - Line 146: Updated consumer output example
   - Line 185: Updated workflow description
   - Line 203: Updated test command
   - Line 239: Updated queue list

8. **docs/PROJECT_STATUS.md**
   - Line 33: Updated feature description

## Migration Notes

### For Local Development (Minikube)
After deploying these changes, you'll need to:

1. **Create new queues in RabbitMQ**:
   ```python
   import pika
   
   credentials = pika.PlainCredentials('admin', 'admin123')
   connection = pika.BlockingConnection(
       pika.ConnectionParameters('localhost', 5672, '/', credentials)
   )
   channel = connection.channel()
   
   # Create new input queue
   channel.queue_declare(queue='document.authentication.requested', durable=True)
   channel.queue_bind(
       exchange='citizen_affiliation',
       queue='document.authentication.requested',
       routing_key='document.authentication.requested'
   )
   
   # Create new success queue
   channel.queue_declare(queue='document.authentication.ready', durable=True)
   channel.queue_bind(
       exchange='citizen_affiliation',
       queue='document.authentication.ready',
       routing_key='document.authentication.ready'
   )
   
   connection.close()
   ```

2. **Delete old queues** (optional, after migration):
   - `document.authentication`
   - `document.auth.success`

3. **Update any external services** that publish to `document.authentication` to use `document.authentication.requested`

4. **Update any services consuming** `document.auth.success` to consume from `document.authentication.ready`

### For AWS EKS Deployment
The changes are already in the code, so when you deploy to AWS EKS, the new queue names will be used automatically. Make sure any external services are updated to use the new event names.

## Testing

Run the test suite to verify all changes:
```bash
python manage.py test apps.documents
```

Expected result: All 13 tests should pass with the new event names.
