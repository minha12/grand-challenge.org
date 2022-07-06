from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.db.models import Count, Q

from grandchallenge.profiles.models import UserProfile
from grandchallenge.profiles.tasks import deactivate_user


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    max_num = 1
    can_delete = False


def deactivate_users(modeladmin, request, queryset):
    for user in queryset:
        deactivate_user.signature(kwargs={"user_pk": user.pk}).apply_async()


deactivate_users.short_description = "Deactivate users"
deactivate_users.allowed_permissions = ("change",)


class UserProfileAdmin(UserAdmin):
    inlines = [UserProfileInline]
    autocomplete_fields = ("groups",)
    readonly_fields = ("user_permissions",)
    list_display = (
        "username",
        "date_joined",
        "email",
        "first_name",
        "last_name",
        "is_staff",
        "has_2fa_enabled",
    )
    list_filter = (
        "is_staff",
        "is_superuser",
        "is_active",
        "user_profile__country",
    )
    actions = (deactivate_users,)

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .annotate(
                totp_device_count=Count(
                    "totpdevice", filter=Q(totpdevice__confirmed=True)
                )
            )
        )

    @admin.display(description="User has 2FA enabled")
    def has_2fa_enabled(self, obj):
        return obj.totp_device_count > 0

    has_2fa_enabled.boolean = True


User = get_user_model()
admin.site.unregister(User)
admin.site.register(User, UserProfileAdmin)
