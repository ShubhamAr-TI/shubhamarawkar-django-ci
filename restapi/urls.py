from django.contrib.auth.views import LogoutView
from django.urls import path,include
from rest_framework.authtoken import views
from rest_framework.routers import DefaultRouter

from restapi.views import UserViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet)

urlpatterns = [
    path('auth/login/', views.obtain_auth_token),
    path('auth/logout/', LogoutView.as_view()),
]
urlpatterns += router.urls

