from django.urls import path
from parallel_logging.views import ProcessLogs, RemoteLogs


urlpatterns = [
    path('process-logs/', ProcessLogs.as_view()),
    path('remote_logging/', RemoteLogs.as_view())
]
