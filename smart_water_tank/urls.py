from django.contrib import admin
from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from water_tank.views import MyDeviceStatusView, SendCommandView, CreateScheduleView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/my-devices/', MyDeviceStatusView.as_view(), name='my_devices'),
    path('api/send-command/', SendCommandView.as_view(), name='send_command'),
    path('api/create-schedule/', CreateScheduleView.as_view(), name='create_schedule'),
]