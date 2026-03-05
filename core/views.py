from datetime import date

from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Employee, Attendance
from .serializers import EmployeeSerializer, AttendanceSerializer


@api_view(["GET"])
def dashboard_stats(request):
    total_employees = Employee.objects.count()
    total_attendance_today = Attendance.objects.filter(date=date.today()).count()
    present_today = Attendance.objects.filter(
        date=date.today(), status=Attendance.STATUS_PRESENT
    ).count()

    top_present = (
        Employee.objects.annotate(
            present_days=Count(
                "attendance_records",
                filter=Q(attendance_records__status=Attendance.STATUS_PRESENT),
            )
        )
        .order_by("-present_days")[:5]
    )

    top_present_data = [
        {
            "id": e.id,
            "employee_id": e.employee_id,
            "full_name": e.full_name,
            "department": e.department,
            "present_days": e.present_days,
        }
        for e in top_present
    ]

    return Response(
        {
            "total_employees": total_employees,
            "total_attendance_today": total_attendance_today,
            "present_today": present_today,
            "top_present": top_present_data,
        }
    )


class EmployeeListCreateView(generics.ListCreateAPIView):
    serializer_class = EmployeeSerializer

    def get_queryset(self):
        qs = Employee.objects.all()
        name = self.request.query_params.get("name", "").strip()
        email = self.request.query_params.get("email", "").strip()
        department = self.request.query_params.get("department", "").strip()

        if name:
            qs = qs.filter(full_name__icontains=name)
        if email:
            qs = qs.filter(email__icontains=email)
        if department:
            qs = qs.filter(department__icontains=department)

        return qs.order_by("full_name")


class EmployeeDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer


class EmployeeAttendanceView(generics.ListAPIView):
    serializer_class = AttendanceSerializer

    def get_queryset(self):
        employee = get_object_or_404(Employee, pk=self.kwargs["pk"])
        return employee.attendance_records.order_by("-date")


class AttendanceListCreateView(generics.ListCreateAPIView):
    serializer_class = AttendanceSerializer

    def get_queryset(self):
        qs = Attendance.objects.select_related("employee").all()
        employee_id = self.request.query_params.get("employee_id")
        if employee_id:
            qs = qs.filter(employee__employee_id=employee_id)

        date_str = self.request.query_params.get("date")
        if date_str:
            try:
                target_date = date.fromisoformat(date_str)
                qs = qs.filter(date=target_date)
            except ValueError:
                pass

        status_filter = self.request.query_params.get("status")
        if status_filter in {Attendance.STATUS_PRESENT, Attendance.STATUS_ABSENT}:
            qs = qs.filter(status=status_filter)

        return qs.order_by("-date", "-created_at")


@api_view(["GET"])
def attendance_overview(request):
    """
    Return one row per employee with current status for the selected date,
    plus total present days overall. This mirrors the original attendance
    overview page behaviour.
    """

    # Base queryset with present_days annotation
    employees_qs = Employee.objects.annotate(
        present_days=Count(
            "attendance_records",
            filter=Q(attendance_records__status=Attendance.STATUS_PRESENT),
        )
    )

    filter_name = request.query_params.get("name", "").strip()
    filter_department = request.query_params.get("department", "").strip()
    filter_status = request.query_params.get("status_filter", "").strip().lower()

    if filter_name:
        employees_qs = employees_qs.filter(full_name__icontains=filter_name)
    if filter_department:
        employees_qs = employees_qs.filter(department__icontains=filter_department)

    employees_qs = employees_qs.order_by("full_name")

    date_str = request.query_params.get("date")
    if not date_str:
        selected_date = date.today()
        date_str = selected_date.isoformat()
    else:
        try:
            selected_date = date.fromisoformat(date_str)
        except ValueError:
            selected_date = date.today()
            date_str = selected_date.isoformat()

    # Existing attendance records for that date
    existing_records = {
        a.employee_id: a
        for a in Attendance.objects.filter(
            date=selected_date, employee__in=employees_qs
        ).select_related("employee")
    }

    rows = []
    for emp in employees_qs:
        record = existing_records.get(emp.id)
        current_status = record.status if record else ""
        current_status_label = record.get_status_display() if record else "Not marked"

        rows.append(
            {
                "id": emp.id,
                "full_name": emp.full_name,
                "department": emp.department,
                "current_status": current_status,
                "current_status_label": current_status_label,
                "present_days": getattr(emp, "present_days", 0),
            }
        )

    # Apply status filter on computed rows
    if filter_status == "present":
        rows = [r for r in rows if r["current_status"] == Attendance.STATUS_PRESENT]
    elif filter_status == "absent":
        rows = [r for r in rows if r["current_status"] == Attendance.STATUS_ABSENT]
    elif filter_status == "not_marked":
        rows = [r for r in rows if not r["current_status"]]

    return Response(rows)


@api_view(["POST"])
def bulk_mark_attendance(request):
    """
    Bulk mark attendance for a given date and list of employee IDs.
    Mirrors the original bulk attendance behavior.
    """

    date_str = request.data.get("date")
    status_value = request.data.get("status")
    employee_ids = request.data.get("employee_ids") or []

    if not date_str:
        return Response({"detail": "date is required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        target_date = date.fromisoformat(date_str)
    except ValueError:
        return Response({"detail": "Invalid date format."}, status=status.HTTP_400_BAD_REQUEST)

    if status_value not in {Attendance.STATUS_PRESENT, Attendance.STATUS_ABSENT}:
        return Response({"detail": "Invalid status."}, status=status.HTTP_400_BAD_REQUEST)

    if not employee_ids:
        return Response({"detail": "employee_ids cannot be empty."}, status=status.HTTP_400_BAD_REQUEST)

    updated_count = 0
    for emp_id in employee_ids:
        try:
            employee = Employee.objects.get(pk=emp_id)
        except Employee.DoesNotExist:
            continue
        Attendance.objects.update_or_create(
            employee=employee,
            date=target_date,
            defaults={"status": status_value},
        )
        updated_count += 1

    return Response({"updated": updated_count}, status=status.HTTP_200_OK)

