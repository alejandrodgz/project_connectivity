#!/usr/bin/env python3
"""
Script to publish a test document authentication message to RabbitMQ.
This simulates an external service sending a document authentication event.
"""

import pika
import json
from datetime import datetime

# RabbitMQ Connection Settings
RABBITMQ_HOST = 'localhost'
RABBITMQ_PORT = 5672
RABBITMQ_USER = 'admin'
RABBITMQ_PASSWORD = 'admin'
RABBITMQ_EXCHANGE = 'citizen_affiliation'
RABBITMQ_QUEUE = 'document.authenticated'
RABBITMQ_ROUTING_KEY = 'document.authenticated'

# Test Message Payload
# This represents a document that has been authenticated
test_message = {
    "event_type": "document_authenticated",
    "timestamp": datetime.utcnow().isoformat(),
    "data": {
        "document_id": "DOC-TEST-001",
        "citizen_id": "1128456232",  # Use the eligible citizen from our tests
        "document_type": "CC",  # Cédula de Ciudadanía
        "document_number": "1128456232",
        "authenticated_at": datetime.utcnow().isoformat(),
        "authentication_method": "biometric",
        "status": "verified",
        "metadata": {
            "ip_address": "192.168.1.100",
            "device": "mobile_app",
            "location": "Bogotá, Colombia"
        }
    }
}

def publish_message():
    """Publish a test message to RabbitMQ"""
    
    print("="*80)
    print("📨 Publishing Document Authentication Message to RabbitMQ")
    print("="*80)
    
    try:
        # Create connection
        credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
        parameters = pika.ConnectionParameters(
            host=RABBITMQ_HOST,
            port=RABBITMQ_PORT,
            credentials=credentials
        )
        
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
        
        # Declare exchange
        channel.exchange_declare(
            exchange=RABBITMQ_EXCHANGE,
            exchange_type='topic',
            durable=True
        )
        
        # Declare queue
        channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True)
        
        # Bind queue to exchange
        channel.queue_bind(
            queue=RABBITMQ_QUEUE,
            exchange=RABBITMQ_EXCHANGE,
            routing_key=RABBITMQ_ROUTING_KEY
        )
        
        # Convert message to JSON
        message_body = json.dumps(test_message, indent=2)
        
        print(f"\n📋 Message Details:")
        print(f"   Exchange: {RABBITMQ_EXCHANGE}")
        print(f"   Queue: {RABBITMQ_QUEUE}")
        print(f"   Routing Key: {RABBITMQ_ROUTING_KEY}")
        print(f"\n📝 Message Payload:")
        print(message_body)
        
        # Publish message
        channel.basic_publish(
            exchange=RABBITMQ_EXCHANGE,
            routing_key=RABBITMQ_ROUTING_KEY,
            body=message_body,
            properties=pika.BasicProperties(
                delivery_mode=2,  # make message persistent
                content_type='application/json'
            )
        )
        
        print(f"\n✅ Message published successfully!")
        print(f"   Timestamp: {test_message['timestamp']}")
        print(f"   Citizen ID: {test_message['data']['citizen_id']}")
        print(f"   Document ID: {test_message['data']['document_id']}")
        
        # Close connection
        connection.close()
        
        print("\n" + "="*80)
        print("✅ Done! Check the consumer logs with:")
        print("   docker logs affiliation-document-consumer --tail 50")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ Error publishing message: {e}")
        print(f"   Make sure RabbitMQ is running and accessible at {RABBITMQ_HOST}:{RABBITMQ_PORT}")
        return False
    
    return True

if __name__ == "__main__":
    publish_message()
