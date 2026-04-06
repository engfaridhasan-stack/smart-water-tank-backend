from django.db import models
from django.contrib.auth.models import User

# ১. মূল ডিভাইস টেবিল
class Device(models.Model):
    device_id = models.CharField(max_length=50, unique=True)
    # এই ফিল্ডটি ইউজারের সাথে ডিভাইসকে লিঙ্ক করে
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='my_devices', null=True, blank=True)
    location = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Device: {self.device_id} | Owner: {self.owner.username if self.owner else 'No Owner'}"

class TankStatus(models.Model):
    device = models.OneToOneField(Device, on_delete=models.CASCADE, related_name='status')
    current_level = models.CharField(max_length=20, default='Unknown') 
    pump_running = models.BooleanField(default=False)
    # এটি নিজে থেকেই প্রতি আপডেটে সময় সেভ করে
    last_heartbeat = models.DateTimeField(auto_now=True) 
    # নতুন ফিল্ড: ডিভাইসটি আসলে অনলাইন কি না তা সেভ রাখবে
    is_online = models.BooleanField(default=False) 

    def __str__(self):
        return f"{self.device.device_id} - {self.current_level}"

# ৩. শিডিউল টেবিল
class PumpSchedule(models.Model):
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='schedules')
    scheduled_time = models.DateTimeField()
    is_executed = models.BooleanField(default=False)