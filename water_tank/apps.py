from django.apps import AppConfig
import os

class WaterTankConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'water_tank'

    def ready(self):
        # জ্যাঙ্গো যাতে ডাবল থ্রেড তৈরি না করে তার জন্য একটি চেক
        # RUN_MAIN চেক করে নিশ্চিত হওয়া যায় যে এটি মেইন প্রসেস কি না
        if os.environ.get('RUN_MAIN') == 'true':
            from . import mqtt_handler
            print("[SYSTEM] Initializing MQTT Connection...")
            mqtt_handler.start_mqtt()