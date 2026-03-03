from django.urls import path
from . import views

urlpatterns = [
    # auth
    path('',        views.home,         name='home'),
    path('signup/', views.signup_view,  name='signup'),
    path('login/',  views.login_view,   name='login'),
    path('logout/', views.logout_view,  name='logout'),

    # student
    path('events/',                         views.event_list,      name='event_list'),
    path('events/<int:pk>/register/',       views.register_event,  name='register_event'),
    path('payment/<int:pk>/upload/',        views.upload_payment,  name='upload_payment'),
    path('my-registrations/',              views.my_registrations, name='my_registrations'),

    # admin
    path('admin-panel/',                       views.admin_dashboard,    name='admin_dashboard'),
    path('admin-panel/events/',                views.admin_events,       name='admin_events'),
    path('admin-panel/events/new/',            views.admin_event_create, name='admin_event_create'),
    path('admin-panel/events/<int:pk>/edit/',  views.admin_event_edit,   name='admin_event_edit'),
    path('admin-panel/events/<int:pk>/toggle/',views.admin_event_toggle, name='admin_event_toggle'),
    path('admin-panel/registrations/',         views.admin_registrations,name='admin_registrations'),
    path('admin-panel/verify/<int:pk>/',       views.admin_verify,       name='admin_verify'),
]
