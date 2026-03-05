from django.urls import path

from . import views


urlpatterns = [
    path("dashboard/", views.dashboard_stats, name="dashboard_stats"),
    path("employees/", views.EmployeeListCreateView.as_view(), name="employees"),
    path("employees/<int:pk>/", views.EmployeeDetailView.as_view(), name="employee_detail"),
    path(
        "employees/<int:pk>/attendance/",
        views.EmployeeAttendanceView.as_view(),
        name="employee_attendance",
    ),
    path("attendance/", views.AttendanceListCreateView.as_view(), name="attendance"),
    path(
        "attendance/overview/",
        views.attendance_overview,
        name="attendance_overview_api",
    ),
    path("attendance/bulk/", views.bulk_mark_attendance, name="attendance_bulk"),
]

