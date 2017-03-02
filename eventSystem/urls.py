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
    url(r'^events/(?P<eventname>[a-zA-Z0-9_ ]+)/questions/$', views.view_questions, name='view_questions'),
    url(r'^create_event/$', views.create_event, name = 'create_event'),
    url(r'^events/(?P<eventname>[a-zA-Z0-9_ ]+)/add_questions/$', views.add_questions, name='add_questions'),
    url(r'^events/(?P<eventname>[a-zA-Z0-9_ ]+)/modify/$', views.modify_event, name = 'modify_event'),
    #url(r'^events/(?P<eventname>[a-zA-Z0-9_ ]+)/submit_questions/$', views.add_questions, name='add_questions'),
    url(r'^events/(?P<eventname>[a-zA-Z0-9_ ]+)/modify_questions/$', views.modify_questions, name='modify_questions'),
    url(r'^add_new_questions/$', views.add_qn_new_event, name='add_qn_new_event')
]
