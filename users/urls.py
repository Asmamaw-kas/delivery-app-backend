from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (CustomTokenObtainPairView, RegisterView, 
                   UserDetailView, UpdateUserView, UserListView)

urlpatterns = [
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('register/', RegisterView.as_view(), name='register'),
    path('me/', UserDetailView.as_view(), name='user_detail'),
    path('update/', UpdateUserView.as_view(), name='update_user'),
    path('users/', UserListView.as_view(), name='user_list'),
    
]