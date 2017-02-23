from django.conf.urls import url, include
from django.contrib.auth import views as auth_views

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    #url(r'^login/$', views.login, name='login'),
    #url('^', include('django.contrib.auth.urls')),
    #url(r'^login/$', auth_views.login),
    url(r'^login/$', views.user_login, name='user_login'),
    url(r'^register/$', views.user_reg, name='user_reg'),
    url(r'^users/(?P<username>[a-zA-Z0-9_]+)/$', views.user_home, name='user_home')
]
