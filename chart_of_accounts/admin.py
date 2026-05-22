from django.contrib import admin

from .models import ChartOfAccount


@admin.register(ChartOfAccount)
class ChartOfAccountAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'group', 'is_party', 'created_at')
    list_filter = ('group', 'is_party')
    search_fields = ('name',)
    ordering = ('id',)
