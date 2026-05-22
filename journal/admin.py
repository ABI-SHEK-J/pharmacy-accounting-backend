from django.contrib import admin

from .models import (
    Journal,
    JournalLine,
    Contra,
    Expense,
    Payment,
    Purchase,
    PurchaseItem,
    PurchaseReturn,
    PurchaseReturnItem,
    Receipt,
    Sale,
    SaleItem,
    SalesReturn,
    SalesReturnItem,
)


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


class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 1


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'date',
        'voucher_no',
        'customer',
        'mode',
        'taxable_amount',
        'gst_amount',
        'round_off_amount',
        'total_amount',
        'debit',
        'credit',
    )
    search_fields = ('voucher_no', 'narration', 'customer__name')
    list_filter = ('date', 'mode', 'gst_applicable')
    ordering = ('-date', '-id')
    inlines = [SaleItemInline]


@admin.register(SaleItem)
class SaleItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'sale', 'medicine', 'batch', 'qty', 'rate', 'gst_percent', 'amount')
    search_fields = ('sale__voucher_no', 'medicine', 'batch', 'hsn')
    list_filter = ('gst_percent',)


class PurchaseItemInline(admin.TabularInline):
    model = PurchaseItem
    extra = 1


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'date',
        'voucher_no',
        'supplier',
        'mode',
        'taxable_amount',
        'gst_amount',
        'round_off_amount',
        'total_amount',
        'debit',
        'credit',
    )
    search_fields = ('voucher_no', 'narration', 'supplier__name')
    list_filter = ('date', 'mode', 'gst_applicable')
    ordering = ('-date', '-id')
    inlines = [PurchaseItemInline]


@admin.register(PurchaseItem)
class PurchaseItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'purchase', 'medicine', 'batch', 'qty', 'rate', 'gst_percent', 'amount')
    search_fields = ('purchase__voucher_no', 'medicine', 'batch', 'hsn')
    list_filter = ('gst_percent',)


class SalesReturnItemInline(admin.TabularInline):
    model = SalesReturnItem
    extra = 1


@admin.register(SalesReturn)
class SalesReturnAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'date',
        'voucher_no',
        'customer',
        'mode',
        'taxable_amount',
        'gst_amount',
        'round_off_amount',
        'total_amount',
        'debit',
        'credit',
    )
    search_fields = ('voucher_no', 'narration', 'customer__name')
    list_filter = ('date', 'mode', 'gst_applicable')
    ordering = ('-date', '-id')
    inlines = [SalesReturnItemInline]


@admin.register(SalesReturnItem)
class SalesReturnItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'sales_return', 'medicine', 'batch', 'qty', 'rate', 'gst_percent', 'amount')
    search_fields = ('sales_return__voucher_no', 'medicine', 'batch', 'hsn')
    list_filter = ('gst_percent',)


class PurchaseReturnItemInline(admin.TabularInline):
    model = PurchaseReturnItem
    extra = 1


@admin.register(PurchaseReturn)
class PurchaseReturnAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'date',
        'voucher_no',
        'supplier',
        'mode',
        'taxable_amount',
        'gst_amount',
        'round_off_amount',
        'total_amount',
        'debit',
        'credit',
    )
    search_fields = ('voucher_no', 'narration', 'supplier__name')
    list_filter = ('date', 'mode', 'gst_applicable')
    ordering = ('-date', '-id')
    inlines = [PurchaseReturnItemInline]


@admin.register(PurchaseReturnItem)
class PurchaseReturnItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'purchase_return', 'medicine', 'batch', 'qty', 'rate', 'gst_percent', 'amount')
    search_fields = ('purchase_return__voucher_no', 'medicine', 'batch', 'hsn')
    list_filter = ('gst_percent',)


@admin.register(Receipt)
class ReceiptAdmin(admin.ModelAdmin):
    list_display = ('id', 'date', 'voucher_no', 'customer', 'mode', 'amount', 'debit', 'credit')
    search_fields = ('voucher_no', 'narration', 'customer__name')
    list_filter = ('date', 'mode')
    ordering = ('-date', '-id')


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'date', 'voucher_no', 'supplier', 'mode', 'amount', 'debit', 'credit')
    search_fields = ('voucher_no', 'narration', 'supplier__name')
    list_filter = ('date', 'mode')
    ordering = ('-date', '-id')


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('id', 'date', 'voucher_no', 'expense_head', 'mode', 'amount', 'debit', 'credit')
    search_fields = ('voucher_no', 'narration', 'expense_head__name')
    list_filter = ('date', 'mode')
    ordering = ('-date', '-id')


@admin.register(Contra)
class ContraAdmin(admin.ModelAdmin):
    list_display = ('id', 'date', 'voucher_no', 'direction', 'amount', 'round_off_amount', 'total_amount', 'debit', 'credit')
    search_fields = ('voucher_no', 'narration')
    list_filter = ('date', 'direction')
    ordering = ('-date', '-id')
