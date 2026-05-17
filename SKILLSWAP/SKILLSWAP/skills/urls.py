from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('add/', views.add_skill, name='add_skill'),
    path('search/', views.search, name='search'),
    path('request/<int:skill_id>/', views.request_exchange, name='request_exchange'),
    path('requests/', views.manage_requests, name='requests'),
    path('accept/<int:id>/', views.accept_request, name='accept_request'),
    path('refuse/<int:id>/', views.refuse_request, name='refuse_request'),
    path('complete/<int:id>/', views.complete_exchange, name='complete_exchange'),
    path('history/', views.history, name='history'),
    path('report/<int:skill_id>/', views.report_skill, name='report_skill'),

    # Admin/Staff pages
    path('admin-panel/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-panel/users/', views.admin_users, name='admin_users'),
    path('admin-panel/users/<int:id>/toggle-active/', views.admin_toggle_active, name='admin_toggle_active'),
    path('admin-panel/skills/', views.admin_skills, name='admin_skills'),
    path('admin-panel/skills/<int:id>/edit/', views.admin_edit_skill, name='admin_edit_skill'),
    path('admin-panel/skills/<int:id>/delete/', views.admin_delete_skill, name='admin_delete_skill'),
    path('admin-panel/requests/', views.admin_requests, name='admin_requests'),
    path('admin-panel/requests/<int:id>/delete/', views.admin_delete_request, name='admin_delete_request'),

    path('moderation/reports/', views.reports_moderation, name='moderation_reports'),
    path('moderation/reports/<int:id>/<str:action>/', views.resolve_report, name='resolve_report'),
]
