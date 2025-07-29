from django.contrib import admin
from django.urls import path, include
from dashboard import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [

    path('admin/', admin.site.urls),
    #
    path('web-twinprocms/', include('dashboard.urls')),
    path('', include('scenes.urls')),
    #TOKENS
    #REFRESH TOKEN 
    path('api/token/access', views.GetAccessTokenView.as_view(), name='refresh-token')
    
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
