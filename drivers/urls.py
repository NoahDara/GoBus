# drivers/urls.py

from django.urls import path
from drivers.views import (
    DriverIndexView,
    DriverDetailView,
    DriverCreateView,
    DriverUpdateView,
    DriverDeleteView,
    CreateUserAccountView,
    DeactivateUserView,
    ActivateUserView,
    ResendWelcomeEmailView,
)

# NO app_name - keep URL names unique without namespace
urlpatterns = [
    # Index and Create
    path('', DriverIndexView.as_view(), name='drivers-index'),
    path('create/', DriverCreateView.as_view(), name='drivers-create'),
    
    # Detail, Update, Delete (using UUID)
    path('<uuid:uid>/', DriverDetailView.as_view(), name='drivers-detail'),
    path('<uuid:uid>/update/', DriverUpdateView.as_view(), name='drivers-update'),
    path('<uuid:uid>/delete/', DriverDeleteView.as_view(), name='drivers-delete'),
    
    # Actions
    path('<uuid:uid>/create-user/', CreateUserAccountView.as_view(), name='drivers-create-user'),
    path('<uuid:uid>/deactivate-user/', DeactivateUserView.as_view(), name='drivers-deactivate-user'),
    path('<uuid:uid>/activate-user/', ActivateUserView.as_view(), name='drivers-activate-user'),
    path('<uuid:uid>/resend-email/', ResendWelcomeEmailView.as_view(), name='drivers-resend-email'),
]