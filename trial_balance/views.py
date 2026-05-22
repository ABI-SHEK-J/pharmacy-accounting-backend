from decimal import Decimal

from django.db.models import Sum
from django.db.models.functions import Coalesce
from rest_framework.decorators import api_view
from rest_framework.response import Response

from chart_of_accounts.models import ChartOfAccount
from journal.models import JournalLine


def split_balance(debit_total, credit_total):
    if debit_total > credit_total:
        return debit_total - credit_total, Decimal('0')
    if credit_total > debit_total:
        return Decimal('0'), credit_total - debit_total
    return Decimal('0'), Decimal('0')


@api_view(['GET'])
def trial_balance(request):
    rows = (
        JournalLine.objects
        .values('account_id')
        .annotate(
            debit_total=Coalesce(Sum('debit'), Decimal('0')),
            credit_total=Coalesce(Sum('credit'), Decimal('0')),
        )
    )
    totals_by_account = {row['account_id']: row for row in rows}

    data = []
    total_debit = Decimal('0')
    total_credit = Decimal('0')

    for account in ChartOfAccount.objects.all().order_by('id'):
        row = totals_by_account.get(account.id)
        if not row:
            continue

        debit, credit = split_balance(row['debit_total'], row['credit_total'])
        if debit == 0 and credit == 0:
            continue

        total_debit += debit
        total_credit += credit

        data.append({
            'account_id': account.id,
            'account': account.name,
            'group': account.group,
            'debit': debit,
            'credit': credit,
        })

    return Response({
        'status': True,
        'data': data,
        'totals': {
            'debit': total_debit,
            'credit': total_credit,
            'is_balanced': total_debit == total_credit,
        },
    })
