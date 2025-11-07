"""
Unit tests for document authentication service.
"""

from django.test import TestCase
from unittest.mock import Mock, patch, MagicMock
from django.utils import timezone

from .models import DocumentAuthentication
from .services import DocumentAuthenticationService


class DocumentAuthenticationModelTestCase(TestCase):
    """Test cases for DocumentAuthentication model."""
    
    def setUp(self):
        """Set up test data."""
        self.test_data = {
            'id_citizen': 1234567890,
            'url_document': 'https://example.com/test.pdf',
            'document_title': 'Test Document'
        }
    
    def test_create_document_authentication(self):
        """Test creating a DocumentAuthentication record."""
        doc_auth = DocumentAuthentication.objects.create(**self.test_data)
        
        self.assertEqual(doc_auth.id_citizen, self.test_data['id_citizen'])
        self.assertEqual(doc_auth.url_document, self.test_data['url_document'])
        self.assertEqual(doc_auth.document_title, self.test_data['document_title'])
        self.assertEqual(doc_auth.status, 'PENDING')
        self.assertFalse(doc_auth.auth_success)
        self.assertIsNotNone(doc_auth.received_at)
        self.assertIsNone(doc_auth.processed_at)
    
    def test_mark_as_success(self):
        """Test marking document authentication as successful."""
        doc_auth = DocumentAuthentication.objects.create(**self.test_data)
        
        response_data = {"message": "Success", "code": "0001"}
        doc_auth.mark_as_success(status_code=200, response_data=response_data)
        
        self.assertEqual(doc_auth.status, 'SUCCESS')
        self.assertTrue(doc_auth.auth_success)
        self.assertEqual(doc_auth.external_api_status_code, 200)
        self.assertEqual(doc_auth.external_api_response, response_data)
        self.assertIsNotNone(doc_auth.processed_at)
    
    def test_mark_as_failed(self):
        """Test marking document authentication as failed."""
        doc_auth = DocumentAuthentication.objects.create(**self.test_data)
        
        doc_auth.mark_as_failed(
            status_code=400,
            error_message="Invalid document",
            response_data={"error": "Document not found"}
        )
        
        self.assertEqual(doc_auth.status, 'FAILED')
        self.assertFalse(doc_auth.auth_success)
        self.assertEqual(doc_auth.external_api_status_code, 400)
        self.assertEqual(doc_auth.error_message, "Invalid document")
        self.assertIsNotNone(doc_auth.processed_at)
    
    def test_mark_as_error(self):
        """Test marking document authentication as error."""
        doc_auth = DocumentAuthentication.objects.create(**self.test_data)
        
        doc_auth.mark_as_error(error_message="Connection timeout")
        
        self.assertEqual(doc_auth.status, 'ERROR')
        self.assertFalse(doc_auth.auth_success)
        self.assertEqual(doc_auth.error_message, "Connection timeout")
        self.assertIsNotNone(doc_auth.processed_at)
    
    def test_mark_event_published(self):
        """Test marking event as published."""
        doc_auth = DocumentAuthentication.objects.create(**self.test_data)
        
        self.assertIsNone(doc_auth.event_published_at)
        doc_auth.mark_event_published()
        
        self.assertIsNotNone(doc_auth.event_published_at)
    
    def test_str_representation(self):
        """Test string representation of model."""
        doc_auth = DocumentAuthentication.objects.create(**self.test_data)
        
        expected = f"Doc Auth - Citizen {self.test_data['id_citizen']} - {self.test_data['document_title']} - PENDING"
        self.assertEqual(str(doc_auth), expected)


class DocumentAuthenticationServiceTestCase(TestCase):
    """Test cases for DocumentAuthenticationService."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_data = {
            'id_citizen': 1234567890,
            'url_document': 'https://example.com/diploma.pdf',
            'document_title': 'Diploma de Grado'
        }
    
    @patch('apps.documents.services.get_rabbitmq_producer')
    @patch('apps.documents.services.get_govcarpeta_client')
    def test_process_authentication_success(self, mock_api_client, mock_producer):
        """Test successful document authentication processing."""
        # Mock API response
        mock_client = Mock()
        mock_client.authenticate_document.return_value = {
            'success': True,
            'status_code': 200,
            'message': 'Authentication successful',
            'data': {'code': '0001', 'message': 'Documento autenticado'}
        }
        mock_api_client.return_value = mock_client
        
        # Mock RabbitMQ producer
        mock_producer_instance = Mock()
        mock_producer.return_value = mock_producer_instance
        
        # Create service instance AFTER mocks are set up
        service = DocumentAuthenticationService()
        
        # Process authentication
        result = service.process_authentication_request(**self.test_data)
        
        # Verify database record
        self.assertIsNotNone(result)
        self.assertEqual(result.id_citizen, self.test_data['id_citizen'])
        self.assertEqual(result.status, 'SUCCESS')
        self.assertTrue(result.auth_success)
        self.assertEqual(result.external_api_status_code, 200)
        
        # Verify API was called
        mock_client.authenticate_document.assert_called_once_with(
            id_citizen=self.test_data['id_citizen'],
            url_document=self.test_data['url_document'],
            document_title=self.test_data['document_title']
        )
        
        # Verify event was published
        mock_producer_instance.publish_event.assert_called_once()
        call_args = mock_producer_instance.publish_event.call_args
        self.assertEqual(call_args.kwargs['routing_key'], 'document.authentication.ready')
        self.assertEqual(call_args.kwargs['event_data']['idCitizen'], self.test_data['id_citizen'])
        self.assertTrue(call_args.kwargs['event_data']['authSuccess'])
    
    @patch('apps.documents.services.get_rabbitmq_producer')
    @patch('apps.documents.services.get_govcarpeta_client')
    def test_process_authentication_failure(self, mock_api_client, mock_producer):
        """Test failed document authentication processing."""
        # Mock API response - failure
        mock_client = Mock()
        mock_client.authenticate_document.return_value = {
            'success': False,
            'status_code': 400,
            'message': 'Invalid document format',
            'data': None
        }
        mock_api_client.return_value = mock_client
        
        # Mock RabbitMQ producer
        mock_producer_instance = Mock()
        mock_producer.return_value = mock_producer_instance
        
        # Create service instance
        service = DocumentAuthenticationService()
        
        # Process authentication
        result = service.process_authentication_request(**self.test_data)
        
        # Verify database record
        self.assertEqual(result.status, 'FAILED')
        self.assertFalse(result.auth_success)
        self.assertEqual(result.external_api_status_code, 400)
        
        # Verify failure event was published
        call_args = mock_producer_instance.publish_event.call_args
        self.assertEqual(call_args.kwargs['routing_key'], 'document.auth.failure')
        self.assertFalse(call_args.kwargs['event_data']['authSuccess'])
    
    @patch('apps.documents.services.get_rabbitmq_producer')
    @patch('apps.documents.services.get_govcarpeta_client')
    def test_process_authentication_api_exception(self, mock_api_client, mock_producer):
        """Test handling of API exceptions."""
        # Mock API to raise exception
        mock_client = Mock()
        mock_client.authenticate_document.side_effect = Exception("Connection timeout")
        mock_api_client.return_value = mock_client
        
        # Mock RabbitMQ producer
        mock_producer_instance = Mock()
        mock_producer.return_value = mock_producer_instance
        
        # Create service instance
        service = DocumentAuthenticationService()
        
        # Process authentication should raise exception
        with self.assertRaises(Exception) as context:
            service.process_authentication_request(**self.test_data)
        
        self.assertIn("Connection timeout", str(context.exception))
        
        # Verify record was marked as error
        doc_auth = DocumentAuthentication.objects.get(id_citizen=self.test_data['id_citizen'])
        self.assertEqual(doc_auth.status, 'ERROR')
        self.assertFalse(doc_auth.auth_success)
        self.assertIn("Connection timeout", doc_auth.error_message)
    
    @patch('apps.documents.services.get_rabbitmq_producer')
    @patch('apps.documents.services.get_govcarpeta_client')
    def test_publish_result_event_success(self, mock_api_client, mock_producer):
        """Test publishing success event."""
        # Mock API response
        mock_client = Mock()
        mock_client.authenticate_document.return_value = {
            'success': True,
            'status_code': 200,
            'message': 'Success',
            'data': {}
        }
        mock_api_client.return_value = mock_client
        
        # Mock RabbitMQ producer
        mock_producer_instance = Mock()
        mock_producer.return_value = mock_producer_instance
        
        # Create service instance
        service = DocumentAuthenticationService()
        
        # Process authentication
        result = service.process_authentication_request(**self.test_data)
        
        # Verify event published timestamp was set
        self.assertIsNotNone(result.event_published_at)
        
        # Verify correct routing key was used
        call_args = mock_producer_instance.publish_event.call_args
        self.assertEqual(call_args.kwargs['routing_key'], 'document.authentication.ready')
    
    @patch('apps.documents.services.get_rabbitmq_producer')
    @patch('apps.documents.services.get_govcarpeta_client')
    def test_publish_result_event_failure(self, mock_api_client, mock_producer):
        """Test publishing failure event."""
        # Mock API response - non-200 status
        mock_client = Mock()
        mock_client.authenticate_document.return_value = {
            'success': False,
            'status_code': 404,
            'message': 'Document not found',
            'data': None
        }
        mock_api_client.return_value = mock_client
        
        # Mock RabbitMQ producer
        mock_producer_instance = Mock()
        mock_producer.return_value = mock_producer_instance
        
        # Create service instance
        service = DocumentAuthenticationService()
        
        # Process authentication
        service.process_authentication_request(**self.test_data)
        
        # Verify failure routing key was used
        call_args = mock_producer_instance.publish_event.call_args
        self.assertEqual(call_args.kwargs['routing_key'], 'document.auth.failure')
        
        # Verify event data structure
        event_data = call_args.kwargs['event_data']
        self.assertEqual(event_data['idCitizen'], self.test_data['id_citizen'])
        self.assertEqual(event_data['UrlDocument'], self.test_data['url_document'])
        self.assertEqual(event_data['documentTitle'], self.test_data['document_title'])
        self.assertFalse(event_data['authSuccess'])
    
    def test_get_authentication_history(self):
        """Test retrieving authentication history for a citizen."""
        # Create multiple records for same citizen
        citizen_id = 1234567890
        DocumentAuthentication.objects.create(
            id_citizen=citizen_id,
            url_document='https://example.com/doc1.pdf',
            document_title='Document 1',
            status='SUCCESS'
        )
        DocumentAuthentication.objects.create(
            id_citizen=citizen_id,
            url_document='https://example.com/doc2.pdf',
            document_title='Document 2',
            status='FAILED'
        )
        
        # Create record for different citizen
        DocumentAuthentication.objects.create(
            id_citizen=9876543210,
            url_document='https://example.com/doc3.pdf',
            document_title='Document 3',
            status='SUCCESS'
        )
        
        # Create service and get history for first citizen
        service = DocumentAuthenticationService()
        history = service.get_authentication_history(citizen_id)
        
        # Verify results
        self.assertEqual(len(history), 2)
        self.assertTrue(all(doc.id_citizen == citizen_id for doc in history))
    
    @patch('apps.documents.services.get_rabbitmq_producer')
    @patch('apps.documents.services.get_govcarpeta_client')
    def test_event_data_format(self, mock_api_client, mock_producer):
        """Test that published event has correct data format."""
        # Mock successful API response
        mock_client = Mock()
        mock_client.authenticate_document.return_value = {
            'success': True,
            'status_code': 200,
            'message': 'Success',
            'data': {}
        }
        mock_api_client.return_value = mock_client
        
        # Mock RabbitMQ producer
        mock_producer_instance = Mock()
        mock_producer.return_value = mock_producer_instance
        
        # Create service instance
        service = DocumentAuthenticationService()
        
        # Process authentication
        service.process_authentication_request(**self.test_data)
        
        # Get published event data
        call_args = mock_producer_instance.publish_event.call_args
        event_data = call_args.kwargs['event_data']
        
        # Verify event structure matches expected format
        self.assertIn('idCitizen', event_data)
        self.assertIn('UrlDocument', event_data)
        self.assertIn('documentTitle', event_data)
        self.assertIn('authSuccess', event_data)
        
        # Verify camelCase naming convention
        self.assertEqual(event_data['idCitizen'], self.test_data['id_citizen'])
        self.assertEqual(event_data['UrlDocument'], self.test_data['url_document'])
        self.assertEqual(event_data['documentTitle'], self.test_data['document_title'])
        self.assertIsInstance(event_data['authSuccess'], bool)
