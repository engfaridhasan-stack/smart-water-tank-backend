from django.apps import AppConfig
import os
import threading

class WaterTankConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'water_tank'

    def ready(self):
        # লোকাল রিলোডার চেক (RUN_MAIN) অথবা রেন্ডার চেক (DAPHNE_RUN)
        # যাতে ডাবল থ্রেড তৈরি না হয়
        if os.environ.get('RUN_MAIN') == 'true' or os.environ.get('DAPHNE_RUN') == 'true' or not os.environ.get('DEBUG'):
            from . import mqtt_handler
            print("[SYSTEM] Initializing MQTT Connection...")
            
            # একটি সেফ থ্রেডে স্টার্ট করা যাতে জ্যাঙ্গোর মেইন প্রসেস আটকে না যায়
            threading.Thread(target=mqtt_handler.start_mqtt, daemon=True).start()