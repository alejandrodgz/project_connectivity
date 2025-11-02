"""
Serializers for affiliation app.
"""

from rest_framework import serializers
from .models import AffiliationCheck


class AffiliationCheckRequestSerializer(serializers.Serializer):
    """Serializer for affiliation check request."""
    
    citizen_id = serializers.CharField(
        required=True,
        max_length=50,
        help_text="Citizen identification number",
        error_messages={
            'required': 'Citizen ID is required',
            'blank': 'Citizen ID cannot be blank'
        }
    )

    def validate_citizen_id(self, value):
        """Validate citizen_id format."""
        # Remove any whitespace
        value = value.strip()
        
        if not value:
            raise serializers.ValidationError("Citizen ID cannot be empty")
        
        # Basic validation - only digits
        if not value.isdigit():
            raise serializers.ValidationError("Citizen ID must contain only numbers")
        
        # Length validation (Colombian IDs are typically 6-10 digits)
        if len(value) < 6 or len(value) > 12:
            raise serializers.ValidationError("Citizen ID must be between 6 and 12 digits")
        
        return value


class AffiliationCheckResponseSerializer(serializers.ModelSerializer):
    """Serializer for simplified affiliation check response."""
    
    is_eligible = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = AffiliationCheck
        fields = [
            'citizen_id',
            'is_eligible',
            'external_api_status_code',
            'citizen_data',
        ]
        read_only_fields = fields


class AffiliationCheckListSerializer(serializers.ModelSerializer):
    """Serializer for listing affiliation checks (without full citizen_data)."""
    
    is_eligible = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = AffiliationCheck
        fields = [
            'id',
            'citizen_id',
            'status',
            'exists_in_system',
            'is_eligible',
            'message',
            'checked_at',
        ]
        read_only_fields = fields
