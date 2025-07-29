from django.contrib import admin
from django.urls import path, include
from scenes import views

urlpatterns = [
    
    #LOGIN AND RESET, SET NEW PASSWORD
    path('login', views.LoginView.as_view(), name='login'),
    path('logout', views.LogoutView.as_view(), name='logout'),
    path('reset-password', views.ResetPasswordView.as_view(), name='reset-password'),
    path('set-new-password/<str:idx>/<str:token>', views.SetNewPasswordView.as_view(), name='set-new-password'),
    #
    path('scene-detail/service/position/', views.ScenePositionUpdateView.as_view(), name='scene-detail-service-position'),
    
]
