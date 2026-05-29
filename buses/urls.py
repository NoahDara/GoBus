# buses/urls.py

from django.urls import path
from . import views

# NO app_name - names are buses-index, buses-detail, etc.

urlpatterns = [
    # List all buses
    path('', views.BusListView.as_view(), name='buses-index'),
    
    # Create new bus
    path('create/', views.BusCreateView.as_view(), name='buses-create'),
    
    # Bus detail (uid-based)
    path('<uuid:uid>/', views.BusDetailView.as_view(), name='buses-detail'),
    
    # Update bus info (uid-based)
    path('<uuid:uid>/update/', views.BusUpdateView.as_view(), name='buses-update'),
    
    # Toggle operational status (uid-based)
    path('<uuid:uid>/toggle-operational/', views.BusToggleOperationalView.as_view(), name='buses-toggle-operational'),
    
    # Reassign driver (uid-based)
    path('<uuid:uid>/reassign-driver/', views.BusReassignDriverView.as_view(), name='buses-reassign-driver'),
]