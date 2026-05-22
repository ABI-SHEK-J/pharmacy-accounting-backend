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
