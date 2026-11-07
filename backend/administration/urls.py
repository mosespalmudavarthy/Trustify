from django.urls import path

from .views import (
    AdministrationDashboardView,
    AdministrationUserListView,
    AdministrationUserDetailView,
    AdministrationUserStatusView,
    AdministrationUserPrivilegesView,
)


urlpatterns = [
    path(
        "dashboard/",
        AdministrationDashboardView.as_view(),
        name="administration-dashboard",
    ),
    path(
        "users/",
        AdministrationUserListView.as_view(),
        name="administration-user-list",
    ),
    path(
        "users/<int:user_id>/",
        AdministrationUserDetailView.as_view(),
        name="administration-user-detail",
    ),
    path(
        "users/<int:user_id>/status/",
        AdministrationUserStatusView.as_view(),
        name="administration-user-status",
    ),
    path(
        "users/<int:user_id>/privileges/",
         AdministrationUserPrivilegesView.as_view(),
         name="administration-user-privileges",
    ),
]