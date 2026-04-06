from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Device, TankStatus, PumpSchedule
from .mqtt_handler import client as mqtt_client

# ১. ইউজারের ডিভাইসের স্ট্যাটাস দেখার জন্য
class MyDeviceStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        devices = Device.objects.filter(owner=request.user)
        data_list = []
        for dev in devices:
            status, _ = TankStatus.objects.get_or_create(device=dev)
            data_list.append({
                "device_id": dev.device_id,
                "level": status.current_level,
                "pump": status.pump_running,
                "last_seen": status.last_heartbeat
            })
        return Response(data_list)

# ২. কমান্ড পাঠানোর জন্য
class SendCommandView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        device_id = request.data.get('device_id')
        command = request.data.get('command') # "1" for ON, "0" for OFF
        try:
            device = Device.objects.get(owner=request.user, device_id=device_id)
            topic = f"CmdInp/{device_id}"
            msg = "ON" if command == "1" else "OFF"
            mqtt_client.publish(topic, msg)
            return Response({"status": "Success", "message": f"Sent {msg}"})
        except Device.DoesNotExist:
            return Response({"status": "Error", "message": "Denied"}, status=403)

# ৩. শিডিউল তৈরি করার জন্য (এটি আপনার urls.py খুঁজছে)
class CreateScheduleView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        device_id = request.data.get('device_id')
        scheduled_time = request.data.get('scheduled_time')
        try:
            device = Device.objects.get(owner=request.user, device_id=device_id)
            PumpSchedule.objects.create(device=device, scheduled_time=scheduled_time)
            return Response({"status": "Success"})
        except Exception as e:
            return Response({"status": "Error", "message": str(e)}, status=400)