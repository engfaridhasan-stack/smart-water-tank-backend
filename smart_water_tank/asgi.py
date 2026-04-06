import os
import django
from django.core.asgi import get_asgi_application

# ১. প্রথমেই সেটিংস এনভায়রনমেন্ট সেট করুন
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_water_tank.settings')

# ২. জ্যাঙ্গোকে সঠিকভাবে লোড হতে দিন
django.setup()

# ৩. জ্যাঙ্গো সেটআপ হওয়ার পর Channels এবং Middleware ইমপোর্ট করুন
from channels.routing import ProtocolTypeRouter, URLRouter
from water_tank.middleware import JwtAuthMiddleware 
import water_tank.routing

# ৪. অ্যাপ্লিকেশন ডিফাইন করুন
application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": JwtAuthMiddleware(
        URLRouter(
            water_tank.routing.websocket_urlpatterns
        )
    ),
})