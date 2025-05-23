"""
Serializers for Hypothesis Mode
"""

from rest_framework import serializers

class HypothesisExplorationSerializer(serializers.Serializer):
    """Serializer for hypothesis exploration requests"""
    question = serializers.CharField(
        required=True,
        min_length=10,
        max_length=2000,
        help_text="The hypothesis or 'what if' question to explore"
    )
    use_advanced_model = serializers.BooleanField(
        required=False,
        default=False,
        help_text="Whether to use advanced model (o3) for reasoning"
    )
    include_sources = serializers.BooleanField(
        required=False,
        default=True,
        help_text="Whether to include source documents in response"
    )

class ProtocolGenerationSerializer(serializers.Serializer):
    """Serializer for protocol generation requests"""
    requirements = serializers.CharField(
        required=True,
        min_length=20,
        max_length=3000,
        help_text="Description of protocol requirements"
    )
    base_protocol_id = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text="Optional ID of existing protocol to modify"
    )
    include_safety = serializers.BooleanField(
        required=False,
        default=True,
        help_text="Whether to include detailed safety warnings"
    )
    format = serializers.ChoiceField(
        choices=['structured', 'narrative', 'checklist'],
        default='structured',
        help_text="Format for the generated protocol"
    )