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
    from water_tank.models import Device, TankStatus # এখানে ইম্পোর্ট ঠিক আছে
    
    try:
        payload_data = json.loads(msg.payload.decode())
        dev_id = payload_data.get("id")
        level = payload_data.get("lvl", "Unknown")
        pump_val = payload_data.get("pmp", 0)

        if not dev_id: return

        is_pump_on = (pump_val == 1)

        # ৩. ডিভাইস খুঁজে বের করা (মালিক সেট করা না থাকলে তৈরি হবে না, শুধু ডাটা আপডেট হবে)
        device, _ = Device.objects.get_or_create(device_id=dev_id)
        
        # ৪. স্ট্যাটাস আপডেট (is_online=True নিশ্চিত করা)
        status, _ = TankStatus.objects.update_or_create(
            device=device,
            defaults={
                'current_level': level,
                'pump_running': is_pump_on,
                'last_heartbeat': timezone.now(),
                'is_online': True 
            }
        )

        # ৫. লাইভ পুশ
        if device.owner:
            channel_layer = get_channel_layer()
            group_name = f"user_group_{device.owner.id}"
            
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    "type": "send_tank_update",
                    "data": {
                        "device_id": dev_id,
                        "current_level": level,
                        "pump_status": is_pump_on,
                        "connection_status": "Online" # সরাসরি অনলাইন পাঠিয়ে দিচ্ছি
                    }
                }
            )
        
        print(f"[SUCCESS] {dev_id} Updated.")

    except Exception as e:
        print(f"[MQTT ERROR] {e}")

def background_worker():
    """শিডিউল চেক করার জন্য অপ্টিমাইজড থ্রেড"""
    # ইম্পোর্ট লুপের বাইরে নিয়ে আসলাম মেমোরি বাঁচাতে
    from water_tank.models import PumpSchedule 
    
    while True:
        try:
            now = timezone.now()
            # ১০ সেকেন্ডের বাফার রেখে চেক করা
            due_schedules = PumpSchedule.objects.filter(
                scheduled_time__lte=now, 
                is_executed=False
            )
            
            for sch in due_schedules:
                target_topic = f"CmdInp/{sch.device.device_id}"
                client.publish(target_topic, "ON")
                
                # আপডেট করা (ডিলিট না করে হিস্ট্রি রাখা ভালো)
                sch.is_executed = True
                sch.save()
                print(f"[SCHEDULE] Executed for {sch.device.device_id}")
                
        except Exception as e:
            print(f"[WORKER ERROR] {e}")
        
        time.sleep(10) # ১০ সেকেন্ড পর পর চেক করলে রেসপন্স ভালো পাওয়া যাবে

# --- বাকি কোড একই থাকবে ---
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