from decimal import Decimal
from datetime import date, datetime

from django.db.models import Sum
from django.db.models.functions import Coalesce
from rest_framework.decorators import api_view
from rest_framework.response import Response

from chart_of_accounts.models import ChartOfAccount
from journal.models import JournalLine


@api_view(['GET'])
def ledgers(request):
    totals = (
        JournalLine.objects
        .values('account_id')
        .annotate(
            debit_total=Coalesce(Sum('debit'), Decimal('0')),
            credit_total=Coalesce(Sum('credit'), Decimal('0')),
        )
    )
    totals_by_account = {
        row['account_id']: row
        for row in totals
    }

    data = []
    for account in ChartOfAccount.objects.all().order_by('id'):
        row = totals_by_account.get(account.id, {})
        debit_total = row.get('debit_total', Decimal('0'))
        credit_total = row.get('credit_total', Decimal('0'))
        debit_balance = Decimal('0')
        credit_balance = Decimal('0')

        if debit_total > credit_total:
            debit_balance = debit_total - credit_total
        elif credit_total > debit_total:
            credit_balance = credit_total - debit_total

        data.append({
            'account_id': account.id,
            'account': account.name,
            'group': account.group,
            'debit': debit_balance,
            'credit': credit_balance,
        })

    return Response({
        'status': True,
        'data': data,
    })


def parse_report_date(value):
    if not value:
        return None
    value = str(value).strip()
    if 'T' in value:
        value = value.split('T')[0]
    for date_format in ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%Y/%m/%d']:
        try:
            return datetime.strptime(value, date_format).date()
        except ValueError:
            pass
    return None


def fy_start_for(day):
    if day.month >= 4:
        return date(day.year, 4, 1)
    return date(day.year - 1, 4, 1)


def range_from_request(request):
    today = date.today()
    filter_type = request.query_params.get('filter', '').lower()

    if filter_type in ['monthly', 'month', 'this_month']:
        return date(today.year, today.month, 1), today

    if filter_type in ['fy', 'financial_year', 'this_fy']:
        return fy_start_for(today), today

    from_date = parse_report_date(
        request.query_params.get('from')
        or request.query_params.get('from_date')
        or request.query_params.get('fromDate')
    )
    to_date = parse_report_date(
        request.query_params.get('to')
        or request.query_params.get('to_date')
        or request.query_params.get('toDate')
    )

    if from_date is None:
        from_date = date(today.year, today.month, 1)
    if to_date is None:
        to_date = today

    return from_date, to_date


def totals_by_account(queryset):
    rows = (
        queryset
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
def period_statement(request):
    from_date, to_date = range_from_request(request)

    if from_date > to_date:
        return Response({
            'status': False,
            'message': 'From date cannot be after To date',
        }, status=400)

    opening_totals = totals_by_account(
        JournalLine.objects.filter(journal__date__lt=from_date)
    )
    period_totals = totals_by_account(
        JournalLine.objects.filter(journal__date__gte=from_date, journal__date__lte=to_date)
    )

    data = []
    totals = {
        'opening_dr': Decimal('0'),
        'opening_cr': Decimal('0'),
        'period_dr': Decimal('0'),
        'period_cr': Decimal('0'),
        'closing_dr': Decimal('0'),
        'closing_cr': Decimal('0'),
    }

    for account in ChartOfAccount.objects.all().order_by('id'):
        opening_row = opening_totals.get(account.id, {})
        period_row = period_totals.get(account.id, {})

        opening_debit_total = opening_row.get('debit_total', Decimal('0'))
        opening_credit_total = opening_row.get('credit_total', Decimal('0'))
        period_dr = period_row.get('debit_total', Decimal('0'))
        period_cr = period_row.get('credit_total', Decimal('0'))

        opening_dr, opening_cr = split_balance(opening_debit_total, opening_credit_total)
        closing_dr, closing_cr = split_balance(
            opening_debit_total + period_dr,
            opening_credit_total + period_cr,
        )

        totals['opening_dr'] += opening_dr
        totals['opening_cr'] += opening_cr
        totals['period_dr'] += period_dr
        totals['period_cr'] += period_cr
        totals['closing_dr'] += closing_dr
        totals['closing_cr'] += closing_cr

        data.append({
            'account_id': account.id,
            'account': account.name,
            'group': account.group,
            'opening_dr': opening_dr,
            'opening_cr': opening_cr,
            'period_dr': period_dr,
            'period_cr': period_cr,
            'closing_dr': closing_dr,
            'closing_cr': closing_cr,
        })

    return Response({
        'status': True,
        'from_date': from_date,
        'to_date': to_date,
        'data': data,
        'totals': totals,
    })
