from django.contrib import admin
from django.utils.html import format_html
from .models import Device, TankStatus, PumpSchedule

# ১. ডিভাইস লিস্ট এবং সার্চ সুবিধা
@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ('device_id', 'owner', 'location', 'created_at')
    list_filter = ('owner',)
    search_fields = ('device_id', 'location')

# ২. রিয়েল-টাইম স্ট্যাটাস মনিটরিং (রঙিন লেভেলসহ)
@admin.register(TankStatus)
class TankStatusAdmin(admin.ModelAdmin):
    # list_display-তে ফাংশনের নামগুলো ঠিকভাবে দেওয়া হয়েছে
    list_display = ('get_device_id', 'get_owner', 'display_level', 'display_pump', 'last_heartbeat')
    
    @admin.display(description='Device ID')
    def get_device_id(self, obj):
        return obj.device.device_id

    @admin.display(description='Owner')
    def get_owner(self, obj):
        return obj.device.owner.username if obj.device.owner else "No Owner"

    # লেভেল অনুযায়ী কালার কোড
    @admin.display(description='Water Level')
    def display_level(self, obj):
        # current_level যদি None হয় তার হ্যান্ডেলিং
        val = str(obj.current_level).upper() if obj.current_level else "UNKNOWN"
        color = "black"
        
        if "FULL" in val: color = "#28a745" # Green
        elif "LOW" in val: color = "#ffc107" # Yellow/Orange
        elif "EMPTY" in val: color = "#dc3545" # Red
        elif "ERROR" in val: color = "#6610f2" # Purple
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            val
        )

    # পাম্পের স্ট্যাটাস ইন্ডিকেটর
    @admin.display(description='Pump')
    def display_pump(self, obj):
        if obj.pump_running:
            return format_html('<b style="color: white; background: #28a745; padding: 2px 8px; border-radius: 4px;">ON</b>')
        return format_html('<b style="color: white; background: #6c757d; padding: 2px 8px; border-radius: 4px;">OFF</b>')

# ৩. শিডিউল ম্যানেজমেন্ট
@admin.register(PumpSchedule)
class PumpScheduleAdmin(admin.ModelAdmin):
    list_display = ('device', 'scheduled_time', 'is_executed')
    list_filter = ('is_executed',)