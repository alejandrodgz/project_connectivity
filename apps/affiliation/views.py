"""
API views for affiliation app.
"""

import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from .serializers import (
    AffiliationCheckRequestSerializer,
    AffiliationCheckResponseSerializer,
    AffiliationCheckListSerializer
)
from .services import AffiliationService

logger = logging.getLogger(__name__)


class AffiliationCheckView(APIView):
    """
    API endpoint for checking citizen affiliation eligibility.
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        request=AffiliationCheckRequestSerializer,
        responses={
            200: AffiliationCheckResponseSerializer,
            204: OpenApiTypes.OBJECT,
            400: OpenApiTypes.OBJECT,
            500: OpenApiTypes.OBJECT,
        },
        description="Check if a citizen is eligible for affiliation by validating against external API",
        tags=['Affiliation']
    )
    def post(self, request):
        """
        Check citizen affiliation eligibility.
        
        Expected payload:
        {
            "citizen_id": "1128456232"
        }
        
        Returns:
        - 200: Citizen is eligible (can create affiliation)
        - 204: Citizen is already affiliated (cannot create affiliation)
        - 400: Invalid request data
        - 500: Internal server error
        """
        # Validate request data
        serializer = AffiliationCheckRequestSerializer(data=request.data)
        if not serializer.is_valid():
            logger.warning(f"Invalid affiliation check request: {serializer.errors}")
            return Response(
                {
                    'error': 'Invalid request data',
                    'details': serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        citizen_id = serializer.validated_data['citizen_id']
        
        try:
            # Perform affiliation check
            service = AffiliationService()
            affiliation_check = service.check_affiliation(citizen_id)
            
            # Serialize response
            response_serializer = AffiliationCheckResponseSerializer(affiliation_check)
            
            # Return different status codes based on eligibility
            if affiliation_check.is_eligible:
                # 200: Citizen CAN be affiliated
                return Response(
                    response_serializer.data,
                    status=status.HTTP_200_OK
                )
            else:
                # 204: Citizen CANNOT be affiliated (already affiliated)
                return Response(
                    response_serializer.data,
                    status=status.HTTP_204_NO_CONTENT
                )
            
        except Exception as e:
            logger.error(
                f"Error processing affiliation check for citizen_id: {citizen_id}. "
                f"Error: {str(e)}",
                exc_info=True
            )
            return Response(
                {
                    'error': 'Internal server error',
                    'message': 'An error occurred while processing your request'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AffiliationHistoryView(APIView):
    """
    API endpoint for retrieving affiliation check history.
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='citizen_id',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Citizen ID to retrieve history for',
                required=True
            )
        ],
        responses={
            200: AffiliationCheckListSerializer(many=True),
            400: OpenApiTypes.OBJECT,
        },
        description="Retrieve affiliation check history for a specific citizen",
        tags=['Affiliation']
    )
    def get(self, request):
        """
        Get affiliation check history for a citizen.
        
        Query parameters:
        - citizen_id: Citizen identification number (required)
        
        Returns:
        - 200: List of affiliation checks
        - 400: Missing citizen_id parameter
        """
        citizen_id = request.query_params.get('citizen_id')
        
        if not citizen_id:
            return Response(
                {
                    'error': 'Missing required parameter',
                    'message': 'citizen_id query parameter is required'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get affiliation history
        service = AffiliationService()
        history = service.get_affiliation_history(citizen_id)
        
        # Serialize response
        serializer = AffiliationCheckListSerializer(history, many=True)
        
        return Response(
            {
                'count': len(history),
                'results': serializer.data
            },
            status=status.HTTP_200_OK
        )
