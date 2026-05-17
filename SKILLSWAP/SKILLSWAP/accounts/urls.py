from django.urls import path, include
from . import views

urlpatterns = [
    path('login/', views.RoleLoginView.as_view(), name='login'),
    path('', include('django.contrib.auth.urls')),
    path('register/', views.register, name='register'),
    path('profile/<int:user_id>/', views.profile, name='profile'),
]
