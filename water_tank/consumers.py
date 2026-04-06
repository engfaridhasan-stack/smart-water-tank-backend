import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from django.utils import timezone
from datetime import timedelta
from channels.db import database_sync_to_async

class TankConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # ইউজারের তথ্য সংগ্রহ
        self.user = self.scope.get("user")
        
        if self.user is None or self.user.is_anonymous:
            await self.close()
        else:
            self.group_name = f"user_group_{self.user.id}"
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            await self.accept()
            
            # কানেক্ট হওয়ার সাথে সাথেই একবার চেক করবে এবং লুপ শুরু করবে
            self.monitor_task = asyncio.create_task(self.check_device_online_status())

    async def disconnect(self, close_code):
        # কানেকশন কাটলে মনিটর টাস্ক বন্ধ করা
        if hasattr(self, 'monitor_task'):
            self.monitor_task.cancel()
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def check_device_online_status(self):
        """ব্যাকএন্ড নিজে থেকে চেক করে অ্যাপে আপডেট পাঠাবে"""
        try:
            while True:
                # ডাটাবেজ থেকে ইউজারের ডিভাইসের বর্তমান অবস্থা আনা
                status_data_list = await self.get_user_devices_status()
                
                for data in status_data_list:
                    # অ্যাপে ডাটা পাঠানো (Flutter app এই ফরম্যাটটিই রিড করবে)
                    await self.send(text_data=json.dumps({
                        "data": {
                            "device_id": data['device_id'],
                            "online": data['online'],
                            "current_level": data['level'],
                            "pump_status": data['pump']
                        }
                    }))
                
                # প্রতি ৩০ সেকেন্ড পর পর চেক করবে
                await asyncio.sleep(30) 
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"Monitor Error: {e}")

    @database_sync_to_async
    def get_user_devices_status(self):
        # Circular Import এড়াতে মেথডের ভেতর ইম্পোর্ট
        from water_tank.models import Device, TankStatus
        
        devices = Device.objects.filter(owner=self.user)
        results = []
        now = timezone.now()
        ten_minutes_ago = now - timedelta(minutes=10)
        
        for dev in devices:
            try:
                # ডিভাইসের স্ট্যাটাস খুঁজে বের করা
                status = TankStatus.objects.get(device=dev)
                
                # শেষ হার্টবিট ১০ মিনিটের বেশি পুরনো কি না চেক করা
                is_currently_online = status.last_heartbeat > ten_minutes_ago
                
                # ডাটাবেজের স্ট্যাটাস যদি বর্তমান অবস্থার সাথে না মিলে, তবে আপডেট করা
                if status.is_online != is_currently_online:
                    status.is_online = is_currently_online
                    status.save(update_fields=['is_online'])
                
                results.append({
                    "device_id": dev.device_id,
                    "online": is_currently_online,
                    "level": status.current_level,
                    "pump": status.pump_running
                })
            except TankStatus.DoesNotExist:
                continue
                
        return results

    async def send_tank_update(self, event):
        """MQTT থেকে রিয়েল-টাইম আপডেট আসলে এই মেথডটি কল হবে"""
        # লাইভ ডাটা সরাসরি পাঠিয়ে দেওয়া
        await self.send(text_data=json.dumps(event['data']))