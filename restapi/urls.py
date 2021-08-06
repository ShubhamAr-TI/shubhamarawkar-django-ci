from django.urls import path
from django.conf.urls import url,include
from rest_framework.authtoken import views
from rest_framework.routers import DefaultRouter

from restapi.views import *

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'categories', CategoryViewSet)
router.register(r'expenses', ExpenseViewSet)
router.register(r'userexpense', UserExpenseViewSet)

urlpatterns = [
    path('auth/login/', views.obtain_auth_token),
    path('auth/logout/', Logout.as_view()),
    path('balances/', Balances.as_view()),
]
urlpatterns += router.urls
