"""
Unit tests for affiliation app.
"""

import json
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken

from apps.affiliation.models import AffiliationCheck
from apps.affiliation.services import AffiliationService
from apps.affiliation.serializers import (
    AffiliationCheckRequestSerializer,
    AffiliationCheckResponseSerializer
)


class AffiliationCheckModelTests(TestCase):
    """Tests for AffiliationCheck model."""
    
    def test_create_affiliation_check_eligible(self):
        """Test creating an affiliation check for eligible citizen."""
        check = AffiliationCheck.objects.create(
            citizen_id="1128456232",
            status="ELIGIBLE",
            exists_in_system=True,
            citizen_data={"name": "John Doe", "id": "1128456232"},
            message="Citizen found and eligible",
            external_api_status_code=200
        )
        
        self.assertEqual(check.citizen_id, "1128456232")
        self.assertEqual(check.status, "ELIGIBLE")
        self.assertTrue(check.exists_in_system)
        self.assertTrue(check.is_eligible)
        self.assertIsNotNone(check.checked_at)
    
    def test_create_affiliation_check_not_found(self):
        """Test creating an affiliation check for non-existent citizen."""
        check = AffiliationCheck.objects.create(
            citizen_id="9999999999",
            status="NOT_FOUND",
            exists_in_system=False,
            message="Citizen does not exist",
            external_api_status_code=204
        )
        
        self.assertEqual(check.status, "NOT_FOUND")
        self.assertFalse(check.exists_in_system)
        self.assertFalse(check.is_eligible)
    
    def test_str_representation(self):
        """Test string representation of AffiliationCheck."""
        check = AffiliationCheck.objects.create(
            citizen_id="1128456232",
            status="ELIGIBLE",
            exists_in_system=True,
            external_api_status_code=200
        )
        
        self.assertIn("1128456232", str(check))
        self.assertIn("ELIGIBLE", str(check))


class AffiliationCheckSerializerTests(TestCase):
    """Tests for affiliation serializers."""
    
    def test_request_serializer_valid_data(self):
        """Test request serializer with valid data."""
        data = {"citizen_id": "1128456232"}
        serializer = AffiliationCheckRequestSerializer(data=data)
        
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['citizen_id'], "1128456232")
    
    def test_request_serializer_invalid_empty(self):
        """Test request serializer with empty citizen_id."""
        data = {"citizen_id": ""}
        serializer = AffiliationCheckRequestSerializer(data=data)
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('citizen_id', serializer.errors)
    
    def test_request_serializer_invalid_non_numeric(self):
        """Test request serializer with non-numeric citizen_id."""
        data = {"citizen_id": "ABC123XYZ"}
        serializer = AffiliationCheckRequestSerializer(data=data)
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('citizen_id', serializer.errors)
    
    def test_request_serializer_invalid_too_short(self):
        """Test request serializer with too short citizen_id."""
        data = {"citizen_id": "12345"}
        serializer = AffiliationCheckRequestSerializer(data=data)
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('citizen_id', serializer.errors)
    
    def test_request_serializer_strips_whitespace(self):
        """Test request serializer strips whitespace."""
        data = {"citizen_id": "  1128456232  "}
        serializer = AffiliationCheckRequestSerializer(data=data)
        
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['citizen_id'], "1128456232")
    
    def test_response_serializer(self):
        """Test response serializer."""
        check = AffiliationCheck.objects.create(
            citizen_id="1128456232",
            status="ELIGIBLE",
            exists_in_system=False,
            citizen_data=None,
            message="Citizen is not affiliated yet and can be registered",
            external_api_status_code=204
        )
        
        serializer = AffiliationCheckResponseSerializer(check)
        data = serializer.data
        
        # Response only has 4 fields
        self.assertEqual(data['citizen_id'], "1128456232")
        self.assertTrue(data['is_eligible'])
        self.assertEqual(data['external_api_status_code'], 204)
        self.assertIsNone(data['citizen_data'])


class AffiliationServiceTests(TestCase):
    """Tests for AffiliationService."""
    
    @patch('apps.affiliation.services.get_govcarpeta_client')
    def test_check_affiliation_citizen_found(self, mock_api_client):
        """Test affiliation check when citizen is found (already affiliated)."""
        # Mock API response - citizen exists (200)
        mock_client = MagicMock()
        mock_client.validate_citizen.return_value = {
            'exists': True,
            'citizen_data': {'name': 'John Doe', 'id': '1128456232'},
            'message': 'Citizen found successfully',
            'status_code': 200
        }
        mock_api_client.return_value = mock_client
        
        # Execute service
        service = AffiliationService()
        result = service.check_affiliation("1128456232")
        
        # Assertions - exists=True means ALREADY_AFFILIATED, NOT eligible
        self.assertEqual(result.citizen_id, "1128456232")
        self.assertEqual(result.status, "ALREADY_AFFILIATED")
        self.assertTrue(result.exists_in_system)
        self.assertFalse(result.is_eligible)
        self.assertEqual(result.external_api_status_code, 200)
        
        # Verify API client was called
        mock_client.validate_citizen.assert_called_once_with("1128456232")
    
    @patch('apps.affiliation.services.get_govcarpeta_client')
    def test_check_affiliation_citizen_not_found(self, mock_api_client):
        """Test affiliation check when citizen is not found (can be affiliated)."""
        # Mock API response for 204 - citizen doesn't exist
        mock_client = MagicMock()
        mock_client.validate_citizen.return_value = {
            'exists': False,
            'citizen_data': None,
            'message': 'Citizen does not exist in the system',
            'status_code': 204
        }
        mock_api_client.return_value = mock_client
        
        # Execute service
        service = AffiliationService()
        result = service.check_affiliation("9999999999")
        
        # Assertions - exists=False means ELIGIBLE to affiliate
        self.assertEqual(result.citizen_id, "9999999999")
        self.assertEqual(result.status, "ELIGIBLE")
        self.assertFalse(result.exists_in_system)
        self.assertTrue(result.is_eligible)
        self.assertEqual(result.external_api_status_code, 204)
    
    @patch('apps.affiliation.services.get_govcarpeta_client')
    def test_check_affiliation_api_error(self, mock_api_client):
        """Test affiliation check when API raises an error."""
        # Mock API to raise exception
        mock_client = MagicMock()
        mock_client.validate_citizen.side_effect = Exception("API connection failed")
        mock_api_client.return_value = mock_client
        
        # Execute service and expect exception
        service = AffiliationService()
        with self.assertRaises(Exception):
            service.check_affiliation("1128456232")
        
        # Verify error record was created
        error_check = AffiliationCheck.objects.filter(
            citizen_id="1128456232",
            status="ERROR"
        ).first()
        
        self.assertIsNotNone(error_check)
        self.assertFalse(error_check.exists_in_system)
        self.assertIn("Error during affiliation check", error_check.message)


class AffiliationAPITests(APITestCase):
    """Tests for affiliation API endpoints."""
    
    def setUp(self):
        """Set up test client and authentication."""
        self.client = APIClient()
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Get JWT token
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        
        # Set authentication header
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
    
    @patch('apps.affiliation.services.get_govcarpeta_client')
    def test_affiliation_check_endpoint_success(self, mock_api_client):
        """Test affiliation check via API when citizen already exists."""
        # Mock API response - citizen exists (200)
        mock_client = MagicMock()
        mock_client.validate_citizen.return_value = {
            'exists': True,
            'citizen_data': {'name': 'John Doe', 'id': '1128456232'},
            'message': 'Citizen found successfully',
            'status_code': 200
        }
        mock_api_client.return_value = mock_client
        
        # Make API request
        url = '/api/v1/affiliation/check/'
        data = {'citizen_id': '1128456232'}
        response = self.client.post(url, data, format='json')
        
        # Assertions - exists=True means NOT eligible, returns 204
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        # 204 responses don't have body in DRF
    
    @patch('apps.affiliation.services.get_govcarpeta_client')
    def test_affiliation_check_endpoint_not_found(self, mock_api_client):
        """Test affiliation check when citizen not found (eligible to affiliate)."""
        # Mock API response for 204 - citizen doesn't exist
        mock_client = MagicMock()
        mock_client.validate_citizen.return_value = {
            'exists': False,
            'citizen_data': None,
            'message': 'Citizen does not exist in the system',
            'status_code': 204
        }
        mock_api_client.return_value = mock_client
        
        # Make API request
        url = '/api/v1/affiliation/check/'
        data = {'citizen_id': '9999999999'}
        response = self.client.post(url, data, format='json')
        
        # Assertions - exists=False means ELIGIBLE, returns 200 OK
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_eligible'])
        self.assertEqual(response.data['citizen_id'], '9999999999')
        self.assertEqual(response.data['external_api_status_code'], 204)
    
    def test_affiliation_check_endpoint_invalid_data(self):
        """Test affiliation check with invalid citizen_id."""
        url = '/api/v1/affiliation/check/'
        data = {'citizen_id': 'ABC123'}
        response = self.client.post(url, data, format='json')
        
        # Assertions
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def test_affiliation_check_endpoint_unauthorized(self):
        """Test affiliation check without authentication."""
        # Remove authentication
        self.client.credentials()
        
        url = '/api/v1/affiliation/check/'
        data = {'citizen_id': '1128456232'}
        response = self.client.post(url, data, format='json')
        
        # Assertions
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_affiliation_check_endpoint_missing_data(self):
        """Test affiliation check with missing citizen_id."""
        url = '/api/v1/affiliation/check/'
        data = {}
        response = self.client.post(url, data, format='json')
        
        # Assertions
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
