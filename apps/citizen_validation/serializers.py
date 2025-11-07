"""
Serializers for affiliation app.
"""

from rest_framework import serializers
from .models import CitizenValidationTrace


class CitizenValidationRequestSerializer(serializers.Serializer):
    """Request serializer for citizen validation."""
    
    citizen_id = serializers.CharField(
        required=True,
        max_length=50,
        help_text="Citizen identification number"
    )

    def validate_citizen_id(self, value):
        """Validate citizen_id format."""
        value = value.strip()
        
        if not value:
            raise serializers.ValidationError("Citizen ID cannot be empty")
        
        if not value.isdigit():
            raise serializers.ValidationError("Citizen ID must contain only numbers")
        
        if len(value) < 6 or len(value) > 12:
            raise serializers.ValidationError("Citizen ID must be between 6 and 12 digits")
        
        return value


class CitizenValidationResponseSerializer(serializers.ModelSerializer):
    """Response serializer for citizen validation."""
    
    is_eligible = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = CitizenValidationTrace
        fields = [
            'citizen_id',
            'is_eligible',
            'external_api_status_code',
        ]
        read_only_fields = fields
