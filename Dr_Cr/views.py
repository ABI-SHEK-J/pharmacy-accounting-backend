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


def split_balance(debit_total, credit_total):
    if debit_total > credit_total:
        return debit_total - credit_total, Decimal('0')
    if credit_total > debit_total:
        return Decimal('0'), credit_total - debit_total
    return Decimal('0'), Decimal('0')


@api_view(['GET'])
def debtors_creditors(request):
    totals = totals_by_account()
    customers = []
    suppliers = []

    party_accounts = ChartOfAccount.objects.filter(is_party=True).order_by('id')
    for account in party_accounts:
        row = totals.get(account.id, {})
        debit_total = row.get('debit_total', Decimal('0'))
        credit_total = row.get('credit_total', Decimal('0'))
        debit_balance, credit_balance = split_balance(debit_total, credit_total)

        if account.group == ChartOfAccount.ASSET and debit_balance > 0:
            customers.append({
                'account_id': account.id,
                'customer': account.name,
                'group': account.group,
                'outstanding': debit_balance,
                'debit': debit_balance,
                'credit': Decimal('0'),
            })

        if account.group == ChartOfAccount.LIABILITY and credit_balance > 0:
            suppliers.append({
                'account_id': account.id,
                'supplier': account.name,
                'group': account.group,
                'payable': credit_balance,
                'debit': Decimal('0'),
                'credit': credit_balance,
            })

    return Response({
        'status': True,
        'customers_debtors': customers,
        'suppliers_creditors': suppliers,
        'summary': {
            'total_receivable': sum(item['outstanding'] for item in customers),
            'total_payable': sum(item['payable'] for item in suppliers),
        },
    })
