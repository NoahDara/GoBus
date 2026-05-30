# buses/urls.py - Complete updated URLs with schedules

from django.urls import path
from . import views

# NO app_name

urlpatterns = [
    # ════ BUSES ════
    path('', views.BusListView.as_view(), name='buses-index'),
    path('create/', views.BusCreateView.as_view(), name='buses-create'),
    path('<uuid:uid>/', views.BusDetailView.as_view(), name='buses-detail'),
    path('<uuid:uid>/update/', views.BusUpdateView.as_view(), name='buses-update'),
    path('<uuid:uid>/toggle-operational/', views.BusToggleOperationalView.as_view(), name='buses-toggle-operational'),
    path('<uuid:uid>/reassign-driver/', views.BusReassignDriverView.as_view(), name='buses-reassign-driver'),
    
    # ════ ROUTES ════
    path('routes/', views.RouteListView.as_view(), name='routes-index'),
    path('routes/create/', views.RouteCreateView.as_view(), name='routes-create'),
    path('routes/<uuid:uid>/', views.RouteDetailView.as_view(), name='routes-detail'),
    path('routes/<uuid:uid>/update/', views.RouteUpdateView.as_view(), name='routes-update'),
    path('routes/<uuid:uid>/delete/', views.RouteDeleteView.as_view(), name='routes-delete'),
    path('routes/<uuid:uid>/delete-reverse/', views.RouteDeleteReverseView.as_view(), name='routes-delete-reverse'),
    
    # ════ ROUTE STOPS ════
    path('routes/<uuid:uid>/stops/create/', views.RouteStopCreateView.as_view(), name='route-stops-create'),
    path('routes/stops/<uuid:uid>/update/', views.RouteStopUpdateView.as_view(), name='route-stops-update'),
    path('routes/stops/<uuid:uid>/delete/', views.RouteStopDeleteView.as_view(), name='route-stops-delete'),
    path('routes/<uuid:uid>/stops/reorder/', views.RouteStopReorderView.as_view(), name='route-stops-reorder'),
    
    # ════ ROUTE SEGMENTS ════
    path('routes/<uuid:uid>/segments/create/', views.RouteSegmentCreateView.as_view(), name='route-segments-create'),
    path('routes/segments/<uuid:uid>/update/', views.RouteSegmentUpdateView.as_view(), name='route-segments-update'),
    path('routes/segments/<uuid:uid>/delete/', views.RouteSegmentDeleteView.as_view(), name='route-segments-delete'),
    
    # ════ SCHEDULES ════
    path('schedules/', views.ScheduleListView.as_view(), name='schedules-index'),
    path('schedules/create/', views.ScheduleCreateView.as_view(), name='schedules-create'),
    path('schedules/<uuid:uid>/', views.ScheduleDetailView.as_view(), name='schedules-detail'),
    path('schedules/<uuid:uid>/status/', views.ScheduleStatusChangeView.as_view(), name='schedules-status'),
    path('schedules/<uuid:uid>/cancel/', views.ScheduleCancelView.as_view(), name='schedules-cancel'),
    
    # AJAX endpoints for dashboard modal booking
    path('api/schedule/<uuid:schedule_uid>/', views.ScheduleDetailAjaxView.as_view(), name='api-schedule-detail'),
    path('api/fare/', views.FareCalculateAjaxView.as_view(), name='api-fare'),
]