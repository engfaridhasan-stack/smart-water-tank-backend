import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from water_tank.middleware import JwtAuthMiddleware  # এটি যোগ করুন
import water_tank.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_water_tank.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": JwtAuthMiddleware(  # AuthMiddlewareStack বদলে এটি দিন
        URLRouter(
            water_tank.routing.websocket_urlpatterns
        )
    ),
})