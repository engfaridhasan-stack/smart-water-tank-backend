import json
import time
import threading
from django.utils import timezone
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
import paho.mqtt.client as mqtt

# MQTT Configuration
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
TOPIC_STATUS = "SmartWaterTank/Status/#"

client = mqtt.Client()

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("[MQTT] Connected to Broker Successfully!")
        client.subscribe(TOPIC_STATUS)
    else:
        print(f"[MQTT] Connection Failed! Return Code: {rc}")

def on_message(client, userdata, msg):
    from water_tank.models import Device, TankStatus
    
    try:
        payload_data = json.loads(msg.payload.decode())
        dev_id = payload_data.get("id")
        level = payload_data.get("lvl", "Unknown")
        pump_val = payload_data.get("pmp", 0)

        if not dev_id: return

        is_pump_on = (pump_val == 1)

        # ডিভাইস নিশ্চিত করা
        device, _ = Device.objects.get_or_create(device_id=dev_id)
        
        # স্ট্যাটাস আপডেট (অ্যাডমিন প্যানেলের এরর এড়াতে str(level) নিশ্চিত করা হয়েছে)
        status, _ = TankStatus.objects.update_or_create(
            device=device,
            defaults={
                'current_level': str(level), 
                'pump_running': is_pump_on,
                'last_heartbeat': timezone.now(),
                'is_online': True 
            }
        )

        # অ্যাপে লাইভ পুশ (আপনার আগের ফরম্যাট ঠিক রেখে)
        if device.owner:
            channel_layer = get_channel_layer()
            group_name = f"user_group_{device.owner.id}"
            
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    "type": "send_tank_update",
                    "data": {
                        "device_id": dev_id,
                        "current_level": str(level),
                        "pump_status": is_pump_on,
                        "connection_status": "Online"
                    }
                }
            )
        
        print(f"[SUCCESS] {dev_id} Updated.")

    except Exception as e:
        print(f"[MQTT ERROR] {e}")

def background_worker():
    from water_tank.models import PumpSchedule 
    while True:
        try:
            now = timezone.now()
            due_schedules = PumpSchedule.objects.filter(
                scheduled_time__lte=now, 
                is_executed=False
            )
            
            for sch in due_schedules:
                target_topic = f"CmdInp/{sch.device.device_id}"
                client.publish(target_topic, "ON")
                sch.is_executed = True
                sch.save()
                print(f"[SCHEDULE] Executed for {sch.device.device_id}")
                
        except Exception as e:
            print(f"[WORKER ERROR] {e}")
        
        time.sleep(10)

client.on_connect = on_connect
client.on_message = on_message

def start_mqtt():
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        mqtt_thread = threading.Thread(target=client.loop_forever, daemon=True)
        worker_thread = threading.Thread(target=background_worker, daemon=True)
        mqtt_thread.start()
        worker_thread.start()
        print("[SYSTEM] MQTT and Worker are running...")
    except Exception as e:
        print(f"[SYSTEM ERROR] {e}")