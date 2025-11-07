"""
API views for affiliation app.

CORE FUNCTIONALITY: Validate citizen existence in external centralizer.
"""

import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema
from drf_spectacular.types import OpenApiTypes

from .serializers import (
    CitizenValidationRequestSerializer,
    CitizenValidationResponseSerializer
)
from .services import CitizenValidationService

logger = logging.getLogger(__name__)


class CitizenValidationView(APIView):
    """
    Validate if a citizen exists in the external centralizer.
    
    Used internally by other services to check citizen existence.
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        request=CitizenValidationRequestSerializer,
        responses={
            200: CitizenValidationResponseSerializer,
            204: OpenApiTypes.OBJECT,
            400: OpenApiTypes.OBJECT,
            500: OpenApiTypes.OBJECT,
        },
        description="Validate citizen existence in external centralizer",
        tags=['Citizen Validation']
    )
    def post(self, request):
        """
        Validate citizen existence.
        
        Returns:
        - 200: Citizen NOT in centralizer (can register)
        - 204: Citizen EXISTS in centralizer (cannot register)
        """
        serializer = CitizenValidationRequestSerializer(data=request.data)
        if not serializer.is_valid():
            logger.warning(f"Invalid request: {serializer.errors}")
            return Response(
                {'error': 'Invalid request data', 'details': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        citizen_id = serializer.validated_data['citizen_id']
        
        try:
            service = CitizenValidationService()
            validation = service.validate_citizen(citizen_id)
            response_serializer = CitizenValidationResponseSerializer(validation)
            
            if validation.is_eligible:
                return Response(response_serializer.data, status=status.HTTP_200_OK)
            else:
                return Response(response_serializer.data, status=status.HTTP_204_NO_CONTENT)
            
        except Exception as e:
            logger.error(f"Error validating citizen {citizen_id}: {str(e)}", exc_info=True)
            return Response(
                {'error': 'Internal server error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
