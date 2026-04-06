from django.urls import path
from . import consumers

websocket_urlpatterns = [
    # এটি যেমন আছে তেমনই থাক
    path('ws/tank-status/', consumers.TankConsumer.as_asgi()),
]