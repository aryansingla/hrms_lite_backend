from rest_framework import serializers

from .models import Employee, Attendance


class EmployeeSerializer(serializers.ModelSerializer):
    present_days = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Employee
        fields = [
            "id",
            "employee_id",
            "full_name",
            "email",
            "department",
            "created_at",
            "present_days",
        ]


class AttendanceSerializer(serializers.ModelSerializer):
    employee_id = serializers.CharField(source="employee.employee_id", read_only=True)
    full_name = serializers.CharField(source="employee.full_name", read_only=True)

    class Meta:
        model = Attendance
        fields = [
            "id",
            "employee",
            "employee_id",
            "full_name",
            "date",
            "status",
            "created_at",
        ]

