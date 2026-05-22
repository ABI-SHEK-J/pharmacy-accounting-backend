from decimal import Decimal

from django.db.models import Sum
from django.db.models.functions import Coalesce
from rest_framework.decorators import api_view
from rest_framework.response import Response

from chart_of_accounts.models import ChartOfAccount
from journal.models import JournalLine


def totals_by_account():
    rows = (
        JournalLine.objects
        .values('account_id')
        .annotate(
            debit_total=Coalesce(Sum('debit'), Decimal('0')),
            credit_total=Coalesce(Sum('credit'), Decimal('0')),
        )
    )
    return {row['account_id']: row for row in rows}


@api_view(['GET'])
def profit_loss(request):
    totals = totals_by_account()
    income = []
    expense = []
    total_income = Decimal('0')
    total_expense = Decimal('0')

    accounts = ChartOfAccount.objects.filter(
        group__in=[ChartOfAccount.INCOME, ChartOfAccount.EXPENSE],
    ).order_by('id')

    for account in accounts:
        row = totals.get(account.id, {})
        debit_total = row.get('debit_total', Decimal('0'))
        credit_total = row.get('credit_total', Decimal('0'))

        if account.group == ChartOfAccount.INCOME:
            amount = credit_total - debit_total
            if amount <= 0:
                continue
            total_income += amount
            income.append({
                'account_id': account.id,
                'account': account.name,
                'group': account.group,
                'amount': amount,
            })

        if account.group == ChartOfAccount.EXPENSE:
            amount = debit_total - credit_total
            if amount <= 0:
                continue
            total_expense += amount
            expense.append({
                'account_id': account.id,
                'account': account.name,
                'group': account.group,
                'amount': amount,
            })

    net_amount = total_income - total_expense
    result_type = 'Profit' if net_amount >= 0 else 'Loss'

    return Response({
        'status': True,
        'income': income,
        'expense': expense,
        'total_income': total_income,
        'total_expense': total_expense,
        'net_profit': net_amount if net_amount >= 0 else Decimal('0'),
        'net_loss': abs(net_amount) if net_amount < 0 else Decimal('0'),
        'result_type': result_type,
        'net_amount': abs(net_amount),
    })
