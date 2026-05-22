from django.contrib import admin

from .models import Journal, JournalLine


class JournalLineInline(admin.TabularInline):
    model = JournalLine
    extra = 1


@admin.register(Journal)
class JournalAdmin(admin.ModelAdmin):
    list_display = ('id', 'date', 'voucher_no', 'narration', 'created_at')
    search_fields = ('voucher_no', 'narration')
    list_filter = ('date',)
    ordering = ('-date', '-id')
    inlines = [JournalLineInline]


@admin.register(JournalLine)
class JournalLineAdmin(admin.ModelAdmin):
    list_display = ('id', 'journal', 'account', 'debit', 'credit')
    search_fields = ('journal__voucher_no', 'account__name')
    list_filter = ('account',)
