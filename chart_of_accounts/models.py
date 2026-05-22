from django.db import models


class ChartOfAccount(models.Model):
    ASSET = 'Asset'
    LIABILITY = 'Liability'
    INCOME = 'Income'
    EXPENSE = 'Expense'
    EQUITY = 'Equity'

    GROUP_CHOICES = [
        (ASSET, 'Asset'),
        (LIABILITY, 'Liability'),
        (INCOME, 'Income'),
        (EXPENSE, 'Expense'),
        (EQUITY, 'Equity'),
    ]

    name = models.CharField(max_length=150, unique=True)
    group = models.CharField(max_length=20, choices=GROUP_CHOICES)
    is_party = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['id']
        verbose_name = 'Chart of Account'
        verbose_name_plural = 'Chart of Accounts'

    def __str__(self):
        return self.name
