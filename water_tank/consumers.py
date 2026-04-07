import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from django.utils import timezone
from datetime import timedelta
from channels.db import database_sync_to_async

class TankConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope.get("user")
        
        if self.user is None or self.user.is_anonymous:
            await self.close()
        else:
            self.group_name = f"user_group_{self.user.id}"
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            await self.accept()
            self.monitor_task = asyncio.create_task(self.check_device_online_status())

    async def disconnect(self, close_code):
        if hasattr(self, 'monitor_task'):
            self.monitor_task.cancel()
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def check_device_online_status(self):
        try:
            while True:
                status_data_list = await self.get_user_devices_status()
                for data in status_data_list:
                    # আপনার অ্যাপের প্রত্যাশিত ফরম্যাট নিশ্চিত করা হয়েছে
                    await self.send(text_data=json.dumps({
                        "data": {
                            "device_id": data['device_id'],
                            "online": data['online'],
                            "current_level": data['level'],
                            "pump_status": data['pump']
                        }
                    }))
                await asyncio.sleep(30) 
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"Monitor Error: {e}")

    @database_sync_to_async
    def get_user_devices_status(self):
        from water_tank.models import Device, TankStatus
        devices = Device.objects.filter(owner=self.user)
        results = []
        now = timezone.now()
        ten_minutes_ago = now - timedelta(minutes=10)
        
        for dev in devices:
            try:
                status = TankStatus.objects.get(device=dev)
                is_currently_online = status.last_heartbeat > ten_minutes_ago
                
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
        """MQTT থেকে আসা লাইভ ডাটা পাঠানোর সময় অ্যাপের ফরম্যাট রক্ষা করা"""
        await self.send(text_data=json.dumps({
            "data": event['data']
        }))