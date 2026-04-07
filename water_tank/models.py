from django.db import models
from django.contrib.auth.models import User

# ১. মূল ডিভাইস টেবিল
class Device(models.Model):
    device_id = models.CharField(max_length=50, unique=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='my_devices', null=True, blank=True)
    location = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        # owner না থাকলে যাতে ক্রাশ না করে সেজন্য হ্যান্ডেলিং
        owner_name = self.owner.username if self.owner else 'No Owner'
        return f"Device: {self.device_id} | Owner: {owner_name}"

# ২. রিয়েল-টাইম স্ট্যাটাস টেবিল
class TankStatus(models.Model):
    device = models.OneToOneField(Device, on_delete=models.CASCADE, related_name='status')
    # max_length ২০ থেকে বাড়িয়ে ৩০ করা হয়েছে যাতে বড় এরর মেসেজ ধরানো যায়
    current_level = models.CharField(max_length=30, default='Unknown') 
    pump_running = models.BooleanField(default=False)
    last_heartbeat = models.DateTimeField(auto_now=True) 
    is_online = models.BooleanField(default=False) 

    def __str__(self):
        # device এর সাথে লিঙ্ক চেক করে নাম দেখানো
        name = self.device.device_id if self.device else "Unknown Device"
        return f"{name} - {self.current_level}"

# ৩. শিডিউল টেবিল
class PumpSchedule(models.Model):
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='schedules')
    scheduled_time = models.DateTimeField()
    is_executed = models.BooleanField(default=False)