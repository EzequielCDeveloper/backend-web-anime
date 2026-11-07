from django.urls import path, include
from rest_framework import routers
from rest_framework_simplejwt.views import TokenRefreshView
from users import views

router = routers.DefaultRouter()
router.register(r'users', views.UserApiViewSet, basename='users')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/me/', views.UserView.as_view(), name='auth_me'),
    path('auth/register/', views.RegisterUserView.as_view({'post': 'create'}), name='auth_register'),
    path('auth/token/', views.ThrottledTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/login/', views.ThrottledTokenObtainPairView.as_view(), name='token_login'),
]
