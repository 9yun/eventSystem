from django.conf.urls import url, include
#from django.contrib.auth import views as auth_views

from . import views
import events

urlpatterns = [
    #url(r'^eventSystem/', include('events.urls')),
    url(r'^$', views.index, name='index'),
    url(r'^login/$', views.user_login, name='user_login'),
    url(r'^logout/$', views.user_logout, name='user_logout'),
    url(r'^register/$', views.user_reg, name='user_reg'),
    url(r'^users/(?P<username>[a-zA-Z0-9_]+)/$', views.user_home, name='user_home'),
    url(r'^events/(?P<eventname>[a-zA-Z0-9_ ]+)/$', views.event_home, name='event_home'),
    url(r'^events/(?P<eventname>[a-zA-Z0-9_]+)/$', views.view_questions, name='view_questions'),
    url(r'^users/(?P<username>[a-zA-Z0-9_]+)/createevent/$', views.create_event, name = 'create_event'),
    url(r'^events/(?P<eventname>[a-zA-Z0-9_ ]+)/modify/$', views.modify_event, name = 'modify_event')
]
