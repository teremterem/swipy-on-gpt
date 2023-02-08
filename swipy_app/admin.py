from django.contrib import admin  # pylint: disable=unused-import

from swipy_app.models import TelegramUpdate


class TelegramUpdateAdmin(admin.ModelAdmin):
    # pylint: disable=protected-access
    readonly_fields = [field.name for field in TelegramUpdate._meta.get_fields()]


admin.site.register(TelegramUpdate, TelegramUpdateAdmin)
