from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import ChartOfAccount


def serialize_chart_of_account(account):
    return {
        'id': account.id,
        'name': account.name,
        'group': account.group,
        'is_party': account.is_party,
        'created_at': account.created_at,
        'updated_at': account.updated_at,
    }


def parse_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ['true', '1', 'yes', 'on']
    return bool(value)


@api_view(['GET'])
def chart_of_accounts(request):
    accounts = ChartOfAccount.objects.all()
    return Response({
        'status': True,
        'data': [serialize_chart_of_account(account) for account in accounts],
    })


@api_view(['POST'])
def create_chart_of_account(request):
    name = request.data.get('name')
    group = request.data.get('group')
    is_party = request.data.get('is_party', False)

    if not name:
        return Response({
            'status': False,
            'message': 'Name is required',
        }, status=status.HTTP_400_BAD_REQUEST)

    valid_groups = [choice[0] for choice in ChartOfAccount.GROUP_CHOICES]
    if group not in valid_groups:
        return Response({
            'status': False,
            'message': 'Group must be Asset, Liability, Income, Expense, or Equity',
        }, status=status.HTTP_400_BAD_REQUEST)

    account = ChartOfAccount.objects.create(
        name=name,
        group=group,
        is_party=parse_bool(is_party),
    )

    return Response({
        'status': True,
        'message': 'Chart of account created successfully',
        'data': serialize_chart_of_account(account),
    }, status=status.HTTP_201_CREATED)
