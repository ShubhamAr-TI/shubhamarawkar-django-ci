from django.urls import path
from rest_framework.authtoken import views
from rest_framework.routers import DefaultRouter
from restapi.views import *

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'category', CategoryViewSet)
router.register(r'expense', ExpenseViewSet)
router.register(r'userexpense', UserExpenseViewSet)


urlpatterns = [
    path('auth/login/', views.obtain_auth_token),
    path('auth/logout/', Logout.as_view()),
]
urlpatterns += router.urls

