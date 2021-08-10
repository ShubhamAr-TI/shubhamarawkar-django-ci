from django.urls import path
from parallel_logging.views import ProcessLogs


urlpatterns = [
    path('process-logs/', ProcessLogs.as_view())     
]