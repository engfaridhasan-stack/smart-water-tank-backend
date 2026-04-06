from rest_framework import serializers
from django.contrib.auth.models import User
from django.utils import timezone
from .models import Device, TankStatus, PumpSchedule

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'password', 'email']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.create_user(**validated_data)
        return user

class TankStatusSerializer(serializers.ModelSerializer):
    pump_status = serializers.BooleanField(source='pump_running')
    last_updated = serializers.DateTimeField(source='last_heartbeat')
    connection_status = serializers.SerializerMethodField() # নতুন লজিক ফিল্ড

    class Meta:
        model = TankStatus
        fields = ['current_level', 'pump_status', 'last_updated', 'connection_status']

    def get_connection_status(self, obj):
        # যদি শেষ হার্টবিট ৩০ মিনিট (১৮০০ সেকেন্ড) এর বেশি আগের হয়
        if obj.last_heartbeat:
            diff = timezone.now() - obj.last_heartbeat
            if diff.total_seconds() > 1800: 
                return "Offline"
            return "Online"
        return "Unknown"

class ScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = PumpSchedule
        fields = ['id', 'scheduled_time']

class DeviceSerializer(serializers.ModelSerializer):
    status = TankStatusSerializer(read_only=True)
    schedules = ScheduleSerializer(many=True, read_only=True)
    
    class Meta:
        model = Device
        fields = ['device_id', 'location', 'status', 'schedules']