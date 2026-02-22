from rest_framework import serializers
from .models import DetectiveBoard

class DetectiveBoardSerializer(serializers.ModelSerializer):
    class Meta:
        model = DetectiveBoard
        fields = ['board_json']
        read_only_fields = ['id', 'detective']
