from django.db import migrations


DEFAULT_ACCOUNTS = [
    ('arun', 'Asset', True),
    ('Bank', 'Asset', False),
    ('Cash', 'Asset', False),
    ('GST Input', 'Asset', False),
    ('Stock', 'Asset', False),
    ('Sundry Debtors', 'Asset', False),
    ('AK Supplier', 'Liability', True),
    ('GST Output', 'Liability', False),
    ('Sundry Creditors', 'Liability', False),
    ('Cash Difference', 'Income', False),
    ('Round Off', 'Income', False),
    ('Sales', 'Income', False),
    ('Sales Return', 'Income', False),
    ('Electricity', 'Expense', False),
    ('Misc Expense', 'Expense', False),
    ('Purchase Return', 'Expense', False),
    ('Purchases', 'Expense', False),
    ('Rent', 'Expense', False),
    ('Salary', 'Expense', False),
    ('Capital', 'Equity', False),
]


def create_default_accounts(apps, schema_editor):
    ChartOfAccount = apps.get_model('chart_of_accounts', 'ChartOfAccount')
    for name, group, is_party in DEFAULT_ACCOUNTS:
        ChartOfAccount.objects.get_or_create(
            name=name,
            defaults={
                'group': group,
                'is_party': is_party,
            },
        )


def remove_default_accounts(apps, schema_editor):
    ChartOfAccount = apps.get_model('chart_of_accounts', 'ChartOfAccount')
    ChartOfAccount.objects.filter(
        name__in=[name for name, group, is_party in DEFAULT_ACCOUNTS],
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('chart_of_accounts', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_default_accounts, remove_default_accounts),
    ]
