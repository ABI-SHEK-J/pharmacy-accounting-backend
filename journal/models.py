from django.db import models

from chart_of_accounts.models import ChartOfAccount


class Journal(models.Model):
    date = models.DateField()
    voucher_no = models.CharField(max_length=50, unique=True)
    narration = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-id']

    def __str__(self):
        return self.voucher_no


class JournalLine(models.Model):
    journal = models.ForeignKey(
        Journal,
        related_name='lines',
        on_delete=models.CASCADE,
    )
    account = models.ForeignKey(
        ChartOfAccount,
        related_name='journal_lines',
        on_delete=models.PROTECT,
    )
    debit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    credit = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f'{self.journal.voucher_no} - {self.account.name}'


class Sale(models.Model):
    CASH = 'Cash'
    BANK = 'Bank'
    CREDIT = 'Credit'

    MODE_CHOICES = [
        (CASH, 'Cash'),
        (BANK, 'Bank'),
        (CREDIT, 'Credit'),
    ]

    date = models.DateField()
    voucher_no = models.CharField(max_length=50, unique=True)
    narration = models.TextField(blank=True, null=True)
    customer = models.ForeignKey(
        ChartOfAccount,
        related_name='sales',
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )
    mode = models.CharField(max_length=20, choices=MODE_CHOICES, default=CASH)
    gst_applicable = models.BooleanField(default=True)
    taxable_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    gst_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    round_off_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    round_off_reason = models.CharField(max_length=255, blank=True, null=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    debit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    credit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    journal = models.OneToOneField(
        Journal,
        related_name='sale',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-id']

    def __str__(self):
        return self.voucher_no


class SaleItem(models.Model):
    sale = models.ForeignKey(
        Sale,
        related_name='items',
        on_delete=models.CASCADE,
    )
    medicine = models.CharField(max_length=150)
    batch = models.CharField(max_length=100, blank=True, null=True)
    expiry = models.DateField(blank=True, null=True)
    hsn = models.CharField(max_length=50, blank=True, null=True)
    qty = models.DecimalField(max_digits=12, decimal_places=2, default=1)
    rate = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    gst_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    taxable_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    gst_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return self.medicine


class Purchase(models.Model):
    CASH = 'Cash'
    BANK = 'Bank'
    CREDIT = 'Credit'

    MODE_CHOICES = [
        (CASH, 'Cash'),
        (BANK, 'Bank'),
        (CREDIT, 'Credit'),
    ]

    date = models.DateField()
    voucher_no = models.CharField(max_length=50, unique=True)
    narration = models.TextField(blank=True, null=True)
    supplier = models.ForeignKey(
        ChartOfAccount,
        related_name='purchases',
        on_delete=models.PROTECT,
    )
    mode = models.CharField(max_length=20, choices=MODE_CHOICES, default=CASH)
    gst_applicable = models.BooleanField(default=True)
    taxable_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    gst_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    round_off_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    round_off_reason = models.CharField(max_length=255, blank=True, null=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    debit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    credit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    journal = models.OneToOneField(
        Journal,
        related_name='purchase',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-id']

    def __str__(self):
        return self.voucher_no


class PurchaseItem(models.Model):
    purchase = models.ForeignKey(
        Purchase,
        related_name='items',
        on_delete=models.CASCADE,
    )
    medicine = models.CharField(max_length=150)
    batch = models.CharField(max_length=100, blank=True, null=True)
    expiry = models.DateField(blank=True, null=True)
    hsn = models.CharField(max_length=50, blank=True, null=True)
    qty = models.DecimalField(max_digits=12, decimal_places=2, default=1)
    rate = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    gst_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    taxable_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    gst_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return self.medicine


class SalesReturn(models.Model):
    CASH = 'Cash'
    BANK = 'Bank'
    CREDIT = 'Credit'

    MODE_CHOICES = [
        (CASH, 'Cash'),
        (BANK, 'Bank'),
        (CREDIT, 'Credit'),
    ]

    date = models.DateField()
    voucher_no = models.CharField(max_length=50, unique=True)
    narration = models.TextField(blank=True, null=True)
    customer = models.ForeignKey(
        ChartOfAccount,
        related_name='sales_returns',
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )
    mode = models.CharField(max_length=20, choices=MODE_CHOICES, default=CASH)
    gst_applicable = models.BooleanField(default=True)
    taxable_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    gst_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    round_off_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    round_off_reason = models.CharField(max_length=255, blank=True, null=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    debit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    credit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    journal = models.OneToOneField(
        Journal,
        related_name='sales_return',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-id']

    def __str__(self):
        return self.voucher_no


class SalesReturnItem(models.Model):
    sales_return = models.ForeignKey(
        SalesReturn,
        related_name='items',
        on_delete=models.CASCADE,
    )
    medicine = models.CharField(max_length=150)
    batch = models.CharField(max_length=100, blank=True, null=True)
    expiry = models.DateField(blank=True, null=True)
    hsn = models.CharField(max_length=50, blank=True, null=True)
    qty = models.DecimalField(max_digits=12, decimal_places=2, default=1)
    rate = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    gst_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    taxable_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    gst_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return self.medicine


class PurchaseReturn(models.Model):
    CASH = 'Cash'
    BANK = 'Bank'
    CREDIT = 'Credit'

    MODE_CHOICES = [
        (CASH, 'Cash'),
        (BANK, 'Bank'),
        (CREDIT, 'Credit'),
    ]

    date = models.DateField()
    voucher_no = models.CharField(max_length=50, unique=True)
    narration = models.TextField(blank=True, null=True)
    supplier = models.ForeignKey(
        ChartOfAccount,
        related_name='purchase_returns',
        on_delete=models.PROTECT,
    )
    mode = models.CharField(max_length=20, choices=MODE_CHOICES, default=CASH)
    gst_applicable = models.BooleanField(default=True)
    taxable_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    gst_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    round_off_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    round_off_reason = models.CharField(max_length=255, blank=True, null=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    debit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    credit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    journal = models.OneToOneField(
        Journal,
        related_name='purchase_return',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-id']

    def __str__(self):
        return self.voucher_no


class PurchaseReturnItem(models.Model):
    purchase_return = models.ForeignKey(
        PurchaseReturn,
        related_name='items',
        on_delete=models.CASCADE,
    )
    medicine = models.CharField(max_length=150)
    batch = models.CharField(max_length=100, blank=True, null=True)
    expiry = models.DateField(blank=True, null=True)
    hsn = models.CharField(max_length=50, blank=True, null=True)
    qty = models.DecimalField(max_digits=12, decimal_places=2, default=1)
    rate = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    gst_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    taxable_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    gst_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return self.medicine


class Receipt(models.Model):
    CASH = 'Cash'
    BANK = 'Bank'

    MODE_CHOICES = [
        (CASH, 'Cash'),
        (BANK, 'Bank / Cheque'),
    ]

    date = models.DateField()
    voucher_no = models.CharField(max_length=50, unique=True)
    narration = models.TextField(blank=True, null=True)
    customer = models.ForeignKey(
        ChartOfAccount,
        related_name='receipts',
        on_delete=models.PROTECT,
    )
    mode = models.CharField(max_length=20, choices=MODE_CHOICES, default=CASH)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    debit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    credit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    journal = models.OneToOneField(
        Journal,
        related_name='receipt',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-id']

    def __str__(self):
        return self.voucher_no


class Payment(models.Model):
    CASH = 'Cash'
    BANK = 'Bank'

    MODE_CHOICES = [
        (CASH, 'Cash'),
        (BANK, 'Bank / Cheque'),
    ]

    date = models.DateField()
    voucher_no = models.CharField(max_length=50, unique=True)
    narration = models.TextField(blank=True, null=True)
    supplier = models.ForeignKey(
        ChartOfAccount,
        related_name='payments',
        on_delete=models.PROTECT,
    )
    mode = models.CharField(max_length=20, choices=MODE_CHOICES, default=CASH)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    debit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    credit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    journal = models.OneToOneField(
        Journal,
        related_name='payment',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-id']

    def __str__(self):
        return self.voucher_no


class Expense(models.Model):
    CASH = 'Cash'
    BANK = 'Bank'

    MODE_CHOICES = [
        (CASH, 'Cash'),
        (BANK, 'Bank / Cheque'),
    ]

    date = models.DateField()
    voucher_no = models.CharField(max_length=50, unique=True)
    narration = models.TextField(blank=True, null=True)
    expense_head = models.ForeignKey(
        ChartOfAccount,
        related_name='expenses',
        on_delete=models.PROTECT,
    )
    mode = models.CharField(max_length=20, choices=MODE_CHOICES, default=CASH)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    debit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    credit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    journal = models.OneToOneField(
        Journal,
        related_name='expense',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-id']

    def __str__(self):
        return self.voucher_no


class Contra(models.Model):
    BANK_TO_CASH = 'Bank to Cash'
    CASH_TO_BANK = 'Cash to Bank'

    DIRECTION_CHOICES = [
        (BANK_TO_CASH, 'Bank -> Cash (withdraw)'),
        (CASH_TO_BANK, 'Cash -> Bank (deposit)'),
    ]

    date = models.DateField()
    voucher_no = models.CharField(max_length=50, unique=True)
    narration = models.TextField(blank=True, null=True)
    direction = models.CharField(max_length=30, choices=DIRECTION_CHOICES, default=BANK_TO_CASH)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    round_off_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    round_off_reason = models.CharField(max_length=255, blank=True, null=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    debit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    credit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    journal = models.OneToOneField(
        Journal,
        related_name='contra',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-id']

    def __str__(self):
        return self.voucher_no
