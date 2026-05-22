from decimal import Decimal, InvalidOperation
from datetime import datetime

from django.db import transaction
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from chart_of_accounts.models import ChartOfAccount
from .models import Journal, JournalLine


def serialize_journal_line(line):
    return {
        'id': line.id,
        'account_id': line.account_id,
        'account_name': line.account.name,
        'debit': line.debit,
        'credit': line.credit,
    }


def serialize_journal(journal):
    return {
        'id': journal.id,
        'date': journal.date,
        'voucher_no': journal.voucher_no,
        'narration': journal.narration,
        'lines': [serialize_journal_line(line) for line in journal.lines.all()],
        'created_at': journal.created_at,
        'updated_at': journal.updated_at,
    }


def parse_amount(value):
    if value in [None, '']:
        return Decimal('0')
    try:
        return Decimal(str(value))
    except InvalidOperation:
        return None


def parse_date_value(value):
    if not value:
        return None
    for date_format in ['%Y-%m-%d', '%d/%m/%Y']:
        try:
            return datetime.strptime(value, date_format).date()
        except ValueError:
            pass
    return None


@api_view(['GET'])
def journals(request):
    journal_list = Journal.objects.prefetch_related('lines__account').all()
    return Response({
        'status': True,
        'data': [serialize_journal(journal) for journal in journal_list],
    })


@api_view(['POST'])
def create_journal(request):
    date = request.data.get('date')
    voucher_no = request.data.get('voucher_no')
    narration = request.data.get('narration', '')
    lines = request.data.get('lines', [])

    if not date:
        return Response({
            'status': False,
            'message': 'Date is required',
        }, status=status.HTTP_400_BAD_REQUEST)

    parsed_date = parse_date_value(date)
    if parsed_date is None:
        return Response({
            'status': False,
            'message': 'Date must be in YYYY-MM-DD or DD/MM/YYYY format',
        }, status=status.HTTP_400_BAD_REQUEST)

    if not voucher_no:
        return Response({
            'status': False,
            'message': 'Voucher No. is required',
        }, status=status.HTTP_400_BAD_REQUEST)

    if not isinstance(lines, list) or len(lines) < 2:
        return Response({
            'status': False,
            'message': 'At least two journal lines are required',
        }, status=status.HTTP_400_BAD_REQUEST)

    prepared_lines = []
    total_debit = Decimal('0')
    total_credit = Decimal('0')

    for line in lines:
        account_id = line.get('account_id')
        debit = parse_amount(line.get('debit'))
        credit = parse_amount(line.get('credit'))

        if not account_id:
            return Response({
                'status': False,
                'message': 'Account is required for every line',
            }, status=status.HTTP_400_BAD_REQUEST)

        if debit is None or credit is None:
            return Response({
                'status': False,
                'message': 'Debit and credit must be valid numbers',
            }, status=status.HTTP_400_BAD_REQUEST)

        if debit < 0 or credit < 0:
            return Response({
                'status': False,
                'message': 'Debit and credit cannot be negative',
            }, status=status.HTTP_400_BAD_REQUEST)

        if debit > 0 and credit > 0:
            return Response({
                'status': False,
                'message': 'One line cannot have both debit and credit',
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            account = ChartOfAccount.objects.get(id=account_id)
        except ChartOfAccount.DoesNotExist:
            return Response({
                'status': False,
                'message': f'Account id {account_id} does not exist',
            }, status=status.HTTP_400_BAD_REQUEST)

        prepared_lines.append({
            'account': account,
            'debit': debit,
            'credit': credit,
        })
        total_debit += debit
        total_credit += credit

    if total_debit <= 0 or total_credit <= 0 or total_debit != total_credit:
        return Response({
            'status': False,
            'message': 'Total debit and total credit must be equal',
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        with transaction.atomic():
            journal = Journal.objects.create(
                date=parsed_date,
                voucher_no=voucher_no,
                narration=narration,
            )
            for line in prepared_lines:
                JournalLine.objects.create(journal=journal, **line)
    except Exception as exc:
        return Response({
            'status': False,
            'message': str(exc),
        }, status=status.HTTP_400_BAD_REQUEST)

    journal = Journal.objects.prefetch_related('lines__account').get(id=journal.id)
    return Response({
        'status': True,
        'message': 'Journal created successfully',
        'data': serialize_journal(journal),
    }, status=status.HTTP_201_CREATED)
