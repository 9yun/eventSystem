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
    url(r'^users/(?P<username>.+)/$', views.user_home, name='user_home'),
    url(r'^events/(?P<eventname>.+)/$', views.event_home, name='event_home'),
    url(r'^events/(?P<eventname>.+)/questions/$', views.view_questions, name='view_questions'),
    url(r'^users/(?P<username>.+)/create_event/$', views.create_event, name = 'create_event'),
    url(r'^events/(?P<eventname>.+)/add_questions/$', views.add_questions, name='add_questions'),
    url(r'^events/(?P<eventname>.+)/modify/$', views.modify_event, name = 'modify_event'),
    #url(r'^events/(?P<eventname>.+)/submit_questions/$', views.add_questions, name='add_questions'),
    url(r'^events/(?P<eventname>.+)/modify_questions/$', views.modify_questions, name='modify_questions'),
    url(r'^modify_qns_script/$', views.get_modify_qns_script),
    url(r'^add_qns_script/$', views.get_add_qns_script),
]
