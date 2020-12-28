from django.contrib import admin
from django.contrib.auth import get_user_model, admin as auth_admin

from .models import Student, Teacher

User = get_user_model()


@admin.register(User)
class UserAdmin(auth_admin.UserAdmin):
    pass


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    pass


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    pass
