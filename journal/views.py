from decimal import Decimal, InvalidOperation
from datetime import datetime

from django.db import transaction
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from chart_of_accounts.models import ChartOfAccount
from .models import (
    Journal,
    JournalLine,
    Contra,
    Expense,
    Payment,
    Purchase,
    PurchaseItem,
    PurchaseReturn,
    PurchaseReturnItem,
    Receipt,
    Sale,
    SaleItem,
    SalesReturn,
    SalesReturnItem,
)


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
    if hasattr(value, 'date'):
        return value.date()
    value = str(value).strip()
    if 'T' in value:
        value = value.split('T')[0]
    for date_format in ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%Y/%m/%d']:
        try:
            return datetime.strptime(value, date_format).date()
        except ValueError:
            pass
    return None


def parse_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ['true', '1', 'yes', 'on']
    return bool(value)


def get_data_value(data, *keys, default=None):
    for key in keys:
        if key in data:
            return data.get(key)
    return default


def extract_id(value):
    if isinstance(value, dict):
        return get_data_value(value, 'id', 'value', 'account_id', 'accountId')
    return value


def extract_name(value):
    if isinstance(value, dict):
        return get_data_value(value, 'name', 'label', 'text', 'title')
    if isinstance(value, str) and not value.isdigit():
        return value
    return None


def money(value):
    return value.quantize(Decimal('0.01'))


def get_account(name, group, is_party=False):
    account, created = ChartOfAccount.objects.get_or_create(
        name=name,
        defaults={
            'group': group,
            'is_party': is_party,
        },
    )
    return account


def get_payment_account(mode, customer):
    if mode == Sale.CASH:
        return get_account('Cash', ChartOfAccount.ASSET)
    if mode == Sale.BANK:
        return get_account('Bank', ChartOfAccount.ASSET)
    return customer


def normalize_sale_mode(mode):
    if not mode:
        return Sale.CASH
    mode_map = {
        'cash': Sale.CASH,
        'bank': Sale.BANK,
        'credit': Sale.CREDIT,
        'customer': Sale.CREDIT,
        'customer account': Sale.CREDIT,
    }
    return mode_map.get(str(mode).strip().lower())


def normalize_purchase_mode(mode):
    if not mode:
        return Purchase.CASH
    mode_map = {
        'cash': Purchase.CASH,
        'bank': Purchase.BANK,
        'credit': Purchase.CREDIT,
        'supplier': Purchase.CREDIT,
        'supplier account': Purchase.CREDIT,
    }
    return mode_map.get(str(mode).strip().lower())


def normalize_sales_return_mode(mode):
    if not mode:
        return SalesReturn.CASH
    mode_map = {
        'cash': SalesReturn.CASH,
        'bank': SalesReturn.BANK,
        'credit': SalesReturn.CREDIT,
        'customer': SalesReturn.CREDIT,
        'customer account': SalesReturn.CREDIT,
    }
    return mode_map.get(str(mode).strip().lower())


def normalize_purchase_return_mode(mode):
    if not mode:
        return PurchaseReturn.CASH
    mode_map = {
        'cash': PurchaseReturn.CASH,
        'bank': PurchaseReturn.BANK,
        'credit': PurchaseReturn.CREDIT,
        'supplier': PurchaseReturn.CREDIT,
        'supplier account': PurchaseReturn.CREDIT,
    }
    return mode_map.get(str(mode).strip().lower())


def normalize_receipt_mode(mode):
    if not mode:
        return Receipt.CASH
    mode_map = {
        'cash': Receipt.CASH,
        'bank': Receipt.BANK,
        'bank / cheque': Receipt.BANK,
        'bank/cheque': Receipt.BANK,
        'cheque': Receipt.BANK,
    }
    return mode_map.get(str(mode).strip().lower())


def normalize_payment_mode(mode):
    if not mode:
        return Payment.CASH
    mode_map = {
        'cash': Payment.CASH,
        'bank': Payment.BANK,
        'bank / cheque': Payment.BANK,
        'bank/cheque': Payment.BANK,
        'cheque': Payment.BANK,
    }
    return mode_map.get(str(mode).strip().lower())


def normalize_expense_mode(mode):
    if not mode:
        return Expense.CASH
    mode_map = {
        'cash': Expense.CASH,
        'bank': Expense.BANK,
        'bank / cheque': Expense.BANK,
        'bank/cheque': Expense.BANK,
        'cheque': Expense.BANK,
    }
    return mode_map.get(str(mode).strip().lower())


def normalize_contra_direction(direction):
    if not direction:
        return Contra.BANK_TO_CASH
    direction_map = {
        'bank to cash': Contra.BANK_TO_CASH,
        'bank -> cash': Contra.BANK_TO_CASH,
        'bank - cash': Contra.BANK_TO_CASH,
        'withdraw': Contra.BANK_TO_CASH,
        'cash to bank': Contra.CASH_TO_BANK,
        'cash -> bank': Contra.CASH_TO_BANK,
        'cash - bank': Contra.CASH_TO_BANK,
        'deposit': Contra.CASH_TO_BANK,
    }
    return direction_map.get(str(direction).strip().lower())


def serialize_sale_item(item):
    return {
        'id': item.id,
        'medicine': item.medicine,
        'batch': item.batch,
        'expiry': item.expiry,
        'hsn': item.hsn,
        'qty': item.qty,
        'rate': item.rate,
        'discount_percent': item.discount_percent,
        'gst_percent': item.gst_percent,
        'taxable_amount': item.taxable_amount,
        'gst_amount': item.gst_amount,
        'amount': item.amount,
    }


def serialize_sale(sale):
    journal_lines = []
    if sale.journal_id and hasattr(sale, 'journal'):
        journal_lines = [serialize_journal_line(line) for line in sale.journal.lines.all()]
    total_debit = sum(line['debit'] for line in journal_lines) if journal_lines else Decimal('0')
    total_credit = sum(line['credit'] for line in journal_lines) if journal_lines else Decimal('0')

    return {
        'id': sale.id,
        'date': sale.date,
        'voucher_no': sale.voucher_no,
        'narration': sale.narration,
        'customer_id': sale.customer_id,
        'customer_name': sale.customer.name if sale.customer else None,
        'mode': sale.mode,
        'gst_applicable': sale.gst_applicable,
        'taxable_amount': sale.taxable_amount,
        'gst_amount': sale.gst_amount,
        'round_off_amount': sale.round_off_amount,
        'round_off_reason': sale.round_off_reason,
        'total_amount': sale.total_amount,
        'debit': sale.debit,
        'credit': sale.credit,
        'journal_id': sale.journal_id,
        'payment_account_id': journal_lines[0]['account_id'] if journal_lines else None,
        'payment_account_name': journal_lines[0]['account_name'] if journal_lines else None,
        'journal_lines': journal_lines,
        'total_debit': total_debit,
        'total_credit': total_credit,
        'is_balanced': total_debit == total_credit,
        'items': [serialize_sale_item(item) for item in sale.items.all()],
        'created_at': sale.created_at,
        'updated_at': sale.updated_at,
    }


def serialize_purchase_item(item):
    return {
        'id': item.id,
        'medicine': item.medicine,
        'batch': item.batch,
        'expiry': item.expiry,
        'hsn': item.hsn,
        'qty': item.qty,
        'rate': item.rate,
        'discount_percent': item.discount_percent,
        'gst_percent': item.gst_percent,
        'taxable_amount': item.taxable_amount,
        'gst_amount': item.gst_amount,
        'amount': item.amount,
    }


def serialize_purchase(purchase):
    journal_lines = []
    if purchase.journal_id and hasattr(purchase, 'journal'):
        journal_lines = [serialize_journal_line(line) for line in purchase.journal.lines.all()]
    total_debit = sum(line['debit'] for line in journal_lines) if journal_lines else Decimal('0')
    total_credit = sum(line['credit'] for line in journal_lines) if journal_lines else Decimal('0')

    return {
        'id': purchase.id,
        'date': purchase.date,
        'voucher_no': purchase.voucher_no,
        'narration': purchase.narration,
        'supplier_id': purchase.supplier_id,
        'supplier_name': purchase.supplier.name if purchase.supplier else None,
        'mode': purchase.mode,
        'gst_applicable': purchase.gst_applicable,
        'taxable_amount': purchase.taxable_amount,
        'gst_amount': purchase.gst_amount,
        'round_off_amount': purchase.round_off_amount,
        'round_off_reason': purchase.round_off_reason,
        'total_amount': purchase.total_amount,
        'debit': purchase.debit,
        'credit': purchase.credit,
        'journal_id': purchase.journal_id,
        'payment_account_id': journal_lines[-1]['account_id'] if journal_lines else None,
        'payment_account_name': journal_lines[-1]['account_name'] if journal_lines else None,
        'journal_lines': journal_lines,
        'total_debit': total_debit,
        'total_credit': total_credit,
        'is_balanced': total_debit == total_credit,
        'items': [serialize_purchase_item(item) for item in purchase.items.all()],
        'created_at': purchase.created_at,
        'updated_at': purchase.updated_at,
    }


def serialize_sales_return_item(item):
    return {
        'id': item.id,
        'medicine': item.medicine,
        'batch': item.batch,
        'expiry': item.expiry,
        'hsn': item.hsn,
        'qty': item.qty,
        'rate': item.rate,
        'discount_percent': item.discount_percent,
        'gst_percent': item.gst_percent,
        'taxable_amount': item.taxable_amount,
        'gst_amount': item.gst_amount,
        'amount': item.amount,
    }


def serialize_sales_return(sales_return):
    journal_lines = []
    if sales_return.journal_id and hasattr(sales_return, 'journal'):
        journal_lines = [serialize_journal_line(line) for line in sales_return.journal.lines.all()]
    total_debit = sum(line['debit'] for line in journal_lines) if journal_lines else Decimal('0')
    total_credit = sum(line['credit'] for line in journal_lines) if journal_lines else Decimal('0')

    return {
        'id': sales_return.id,
        'date': sales_return.date,
        'voucher_no': sales_return.voucher_no,
        'narration': sales_return.narration,
        'customer_id': sales_return.customer_id,
        'customer_name': sales_return.customer.name if sales_return.customer else None,
        'mode': sales_return.mode,
        'gst_applicable': sales_return.gst_applicable,
        'taxable_amount': sales_return.taxable_amount,
        'gst_amount': sales_return.gst_amount,
        'round_off_amount': sales_return.round_off_amount,
        'round_off_reason': sales_return.round_off_reason,
        'total_amount': sales_return.total_amount,
        'debit': sales_return.debit,
        'credit': sales_return.credit,
        'journal_id': sales_return.journal_id,
        'payment_account_id': journal_lines[-1]['account_id'] if journal_lines else None,
        'payment_account_name': journal_lines[-1]['account_name'] if journal_lines else None,
        'journal_lines': journal_lines,
        'total_debit': total_debit,
        'total_credit': total_credit,
        'is_balanced': total_debit == total_credit,
        'items': [serialize_sales_return_item(item) for item in sales_return.items.all()],
        'created_at': sales_return.created_at,
        'updated_at': sales_return.updated_at,
    }


def serialize_purchase_return_item(item):
    return {
        'id': item.id,
        'medicine': item.medicine,
        'batch': item.batch,
        'expiry': item.expiry,
        'hsn': item.hsn,
        'qty': item.qty,
        'rate': item.rate,
        'discount_percent': item.discount_percent,
        'gst_percent': item.gst_percent,
        'taxable_amount': item.taxable_amount,
        'gst_amount': item.gst_amount,
        'amount': item.amount,
    }


def serialize_purchase_return(purchase_return):
    journal_lines = []
    if purchase_return.journal_id and hasattr(purchase_return, 'journal'):
        journal_lines = [serialize_journal_line(line) for line in purchase_return.journal.lines.all()]
    total_debit = sum(line['debit'] for line in journal_lines) if journal_lines else Decimal('0')
    total_credit = sum(line['credit'] for line in journal_lines) if journal_lines else Decimal('0')

    return {
        'id': purchase_return.id,
        'date': purchase_return.date,
        'voucher_no': purchase_return.voucher_no,
        'narration': purchase_return.narration,
        'supplier_id': purchase_return.supplier_id,
        'supplier_name': purchase_return.supplier.name if purchase_return.supplier else None,
        'mode': purchase_return.mode,
        'gst_applicable': purchase_return.gst_applicable,
        'taxable_amount': purchase_return.taxable_amount,
        'gst_amount': purchase_return.gst_amount,
        'round_off_amount': purchase_return.round_off_amount,
        'round_off_reason': purchase_return.round_off_reason,
        'total_amount': purchase_return.total_amount,
        'debit': purchase_return.debit,
        'credit': purchase_return.credit,
        'journal_id': purchase_return.journal_id,
        'payment_account_id': journal_lines[0]['account_id'] if journal_lines else None,
        'payment_account_name': journal_lines[0]['account_name'] if journal_lines else None,
        'journal_lines': journal_lines,
        'total_debit': total_debit,
        'total_credit': total_credit,
        'is_balanced': total_debit == total_credit,
        'items': [serialize_purchase_return_item(item) for item in purchase_return.items.all()],
        'created_at': purchase_return.created_at,
        'updated_at': purchase_return.updated_at,
    }


def serialize_receipt(receipt):
    journal_lines = []
    if receipt.journal_id and hasattr(receipt, 'journal'):
        journal_lines = [serialize_journal_line(line) for line in receipt.journal.lines.all()]
    total_debit = sum(line['debit'] for line in journal_lines) if journal_lines else Decimal('0')
    total_credit = sum(line['credit'] for line in journal_lines) if journal_lines else Decimal('0')

    return {
        'id': receipt.id,
        'date': receipt.date,
        'voucher_no': receipt.voucher_no,
        'narration': receipt.narration,
        'customer_id': receipt.customer_id,
        'customer_name': receipt.customer.name if receipt.customer else None,
        'mode': receipt.mode,
        'amount': receipt.amount,
        'debit': receipt.debit,
        'credit': receipt.credit,
        'journal_id': receipt.journal_id,
        'payment_account_id': journal_lines[0]['account_id'] if journal_lines else None,
        'payment_account_name': journal_lines[0]['account_name'] if journal_lines else None,
        'journal_lines': journal_lines,
        'total_debit': total_debit,
        'total_credit': total_credit,
        'is_balanced': total_debit == total_credit,
        'created_at': receipt.created_at,
        'updated_at': receipt.updated_at,
    }


def serialize_payment(payment):
    journal_lines = []
    if payment.journal_id and hasattr(payment, 'journal'):
        journal_lines = [serialize_journal_line(line) for line in payment.journal.lines.all()]
    total_debit = sum(line['debit'] for line in journal_lines) if journal_lines else Decimal('0')
    total_credit = sum(line['credit'] for line in journal_lines) if journal_lines else Decimal('0')

    return {
        'id': payment.id,
        'date': payment.date,
        'voucher_no': payment.voucher_no,
        'narration': payment.narration,
        'supplier_id': payment.supplier_id,
        'supplier_name': payment.supplier.name if payment.supplier else None,
        'mode': payment.mode,
        'amount': payment.amount,
        'debit': payment.debit,
        'credit': payment.credit,
        'journal_id': payment.journal_id,
        'payment_account_id': journal_lines[-1]['account_id'] if journal_lines else None,
        'payment_account_name': journal_lines[-1]['account_name'] if journal_lines else None,
        'journal_lines': journal_lines,
        'total_debit': total_debit,
        'total_credit': total_credit,
        'is_balanced': total_debit == total_credit,
        'created_at': payment.created_at,
        'updated_at': payment.updated_at,
    }


def serialize_expense(expense):
    journal_lines = []
    if expense.journal_id and hasattr(expense, 'journal'):
        journal_lines = [serialize_journal_line(line) for line in expense.journal.lines.all()]
    total_debit = sum(line['debit'] for line in journal_lines) if journal_lines else Decimal('0')
    total_credit = sum(line['credit'] for line in journal_lines) if journal_lines else Decimal('0')

    return {
        'id': expense.id,
        'date': expense.date,
        'voucher_no': expense.voucher_no,
        'narration': expense.narration,
        'expense_head_id': expense.expense_head_id,
        'expense_head_name': expense.expense_head.name if expense.expense_head else None,
        'mode': expense.mode,
        'amount': expense.amount,
        'debit': expense.debit,
        'credit': expense.credit,
        'journal_id': expense.journal_id,
        'payment_account_id': journal_lines[-1]['account_id'] if journal_lines else None,
        'payment_account_name': journal_lines[-1]['account_name'] if journal_lines else None,
        'journal_lines': journal_lines,
        'total_debit': total_debit,
        'total_credit': total_credit,
        'is_balanced': total_debit == total_credit,
        'created_at': expense.created_at,
        'updated_at': expense.updated_at,
    }


def serialize_contra(contra):
    journal_lines = []
    if contra.journal_id and hasattr(contra, 'journal'):
        journal_lines = [serialize_journal_line(line) for line in contra.journal.lines.all()]
    total_debit = sum(line['debit'] for line in journal_lines) if journal_lines else Decimal('0')
    total_credit = sum(line['credit'] for line in journal_lines) if journal_lines else Decimal('0')

    return {
        'id': contra.id,
        'date': contra.date,
        'voucher_no': contra.voucher_no,
        'narration': contra.narration,
        'direction': contra.direction,
        'amount': contra.amount,
        'round_off_amount': contra.round_off_amount,
        'round_off_reason': contra.round_off_reason,
        'total_amount': contra.total_amount,
        'debit': contra.debit,
        'credit': contra.credit,
        'journal_id': contra.journal_id,
        'journal_lines': journal_lines,
        'total_debit': total_debit,
        'total_credit': total_credit,
        'is_balanced': total_debit == total_credit,
        'created_at': contra.created_at,
        'updated_at': contra.updated_at,
    }


def prepare_sale_items(items, gst_applicable):
    if not isinstance(items, list) or not items:
        return None, 'At least one sale item is required'

    prepared_items = []
    taxable_total = Decimal('0')
    gst_total = Decimal('0')

    for item in items:
        medicine = item.get('medicine')
        if not medicine:
            return None, 'Medicine is required for every item'

        qty = parse_amount(item.get('qty', 1))
        rate = parse_amount(item.get('rate', 0))
        discount_percent = parse_amount(get_data_value(
            item,
            'discount_percent',
            'discountPercent',
            'disc_percent',
            'discPercent',
            'discount',
            default=0,
        ))
        gst_percent = parse_amount(get_data_value(
            item,
            'gst_percent',
            'gstPercent',
            'gst',
            default=0,
        ))

        if None in [qty, rate, discount_percent, gst_percent]:
            return None, 'Qty, rate, discount, and GST must be valid numbers'

        if qty <= 0 or rate < 0 or discount_percent < 0 or gst_percent < 0:
            return None, 'Qty must be positive and amounts cannot be negative'

        expiry = item.get('expiry')
        parsed_expiry = parse_date_value(expiry) if expiry else None
        if expiry and parsed_expiry is None:
            return None, 'Expiry must be in YYYY-MM-DD or DD/MM/YYYY format'

        gross = qty * rate
        discount_amount = gross * discount_percent / Decimal('100')
        taxable_amount = money(gross - discount_amount)
        gst_amount = money(taxable_amount * gst_percent / Decimal('100')) if gst_applicable else Decimal('0.00')
        amount = money(taxable_amount + gst_amount)

        prepared_items.append({
            'medicine': medicine,
            'batch': item.get('batch', ''),
            'expiry': parsed_expiry,
            'hsn': item.get('hsn', ''),
            'qty': qty,
            'rate': rate,
            'discount_percent': discount_percent,
            'gst_percent': gst_percent if gst_applicable else Decimal('0'),
            'taxable_amount': taxable_amount,
            'gst_amount': gst_amount,
            'amount': amount,
        })
        taxable_total += taxable_amount
        gst_total += gst_amount

    return {
        'items': prepared_items,
        'taxable_amount': money(taxable_total),
        'gst_amount': money(gst_total),
    }, None


def prepare_purchase_items(items, gst_applicable):
    return prepare_sale_items(items, gst_applicable)


def prepare_sales_return_items(items, gst_applicable):
    return prepare_sale_items(items, gst_applicable)


def prepare_purchase_return_items(items, gst_applicable):
    return prepare_sale_items(items, gst_applicable)


def save_sale_journal(sale):
    sales_account = get_account('Sales', ChartOfAccount.INCOME)
    gst_output_account = get_account('GST Output', ChartOfAccount.LIABILITY)
    round_off_account = get_account('Round Off', ChartOfAccount.INCOME)
    payment_account = get_payment_account(sale.mode, sale.customer)

    if payment_account is None:
        raise ValueError('Customer is required when mode is Credit')

    if sale.journal:
        journal = sale.journal
        journal.date = sale.date
        journal.voucher_no = sale.voucher_no
        journal.narration = sale.narration
        journal.save()
        journal.lines.all().delete()
    else:
        journal = Journal.objects.create(
            date=sale.date,
            voucher_no=sale.voucher_no,
            narration=sale.narration,
        )
        sale.journal = journal
        sale.save(update_fields=['journal'])

    JournalLine.objects.create(
        journal=journal,
        account=payment_account,
        debit=sale.total_amount,
        credit=0,
    )
    if sale.round_off_amount > 0:
        JournalLine.objects.create(
            journal=journal,
            account=round_off_account,
            debit=sale.round_off_amount,
            credit=0,
        )
    JournalLine.objects.create(
        journal=journal,
        account=sales_account,
        debit=0,
        credit=sale.taxable_amount,
    )
    if sale.gst_amount > 0:
        JournalLine.objects.create(
            journal=journal,
            account=gst_output_account,
            debit=0,
            credit=sale.gst_amount,
        )
    if sale.round_off_amount < 0:
        JournalLine.objects.create(
            journal=journal,
            account=round_off_account,
            debit=0,
            credit=abs(sale.round_off_amount),
        )


def save_sale_from_request(data, sale=None):
    date = get_data_value(data, 'date', 'Date')
    parsed_date = parse_date_value(date)
    if parsed_date is None:
        return None, 'Date must be in YYYY-MM-DD, DD/MM/YYYY, DD-MM-YYYY, or YYYY/MM/DD format'

    voucher_no = get_data_value(data, 'voucher_no', 'voucherNo', 'Voucher No.', 'voucher_no')
    if not voucher_no:
        return None, 'Voucher No. is required'

    mode = normalize_sale_mode(get_data_value(data, 'mode', 'payment_mode', 'paymentMode', default=Sale.CASH))
    if mode is None:
        return None, 'Mode must be Cash, Bank, Credit, or Customer'

    customer = None
    customer_id = extract_id(get_data_value(
        data,
        'customer_id',
        'customerId',
        'customer',
        'party_id',
        'partyId',
        'party',
        'account_id',
        'accountId',
    ))
    if customer_id:
        try:
            customer = ChartOfAccount.objects.get(id=customer_id)
        except ChartOfAccount.DoesNotExist:
            return None, f'Customer id {customer_id} does not exist'

    if mode == Sale.CREDIT and customer is None:
        return None, 'Customer is required when mode is Credit'

    gst_applicable = parse_bool(get_data_value(data, 'gst_applicable', 'gstApplicable', default=True))
    prepared, error = prepare_sale_items(get_data_value(data, 'items', 'lines', default=[]), gst_applicable)
    if error:
        return None, error

    round_off_amount = parse_amount(get_data_value(data, 'round_off_amount', 'roundOffAmount', default=0))
    if round_off_amount is None:
        return None, 'Round off amount must be a valid number'

    total_amount = money(prepared['taxable_amount'] + prepared['gst_amount'] - round_off_amount)
    if total_amount < 0:
        return None, 'Total amount cannot be negative'
    debit = parse_amount(get_data_value(data, 'debit', 'Debit', default=total_amount))
    credit = parse_amount(get_data_value(data, 'credit', 'Credit', default=total_amount))

    if debit is None or credit is None:
        return None, 'Debit and credit must be valid numbers'

    debit = money(debit)
    credit = money(credit)

    if debit != credit:
        return None, 'Debit and credit must be equal for sales voucher'

    try:
        with transaction.atomic():
            if sale is None:
                sale = Sale.objects.create(
                    date=parsed_date,
                    voucher_no=voucher_no,
                    narration=get_data_value(data, 'narration', 'Narration', default=''),
                    customer=customer,
                    mode=mode,
                    gst_applicable=gst_applicable,
                    taxable_amount=prepared['taxable_amount'],
                    gst_amount=prepared['gst_amount'],
                    round_off_amount=money(round_off_amount),
                    round_off_reason=get_data_value(data, 'round_off_reason', 'roundOffReason', default=''),
                    total_amount=total_amount,
                    debit=debit,
                    credit=credit,
                )
            else:
                sale.date = parsed_date
                sale.voucher_no = voucher_no
                sale.narration = get_data_value(data, 'narration', 'Narration', default='')
                sale.customer = customer
                sale.mode = mode
                sale.gst_applicable = gst_applicable
                sale.taxable_amount = prepared['taxable_amount']
                sale.gst_amount = prepared['gst_amount']
                sale.round_off_amount = money(round_off_amount)
                sale.round_off_reason = get_data_value(data, 'round_off_reason', 'roundOffReason', default='')
                sale.total_amount = total_amount
                sale.debit = debit
                sale.credit = credit
                sale.save()
                sale.items.all().delete()

            for item in prepared['items']:
                SaleItem.objects.create(sale=sale, **item)

            save_sale_journal(sale)
    except Exception as exc:
        return None, str(exc)

    return (
        Sale.objects.select_related('customer', 'journal')
        .prefetch_related('items', 'journal__lines__account')
        .get(id=sale.id)
    ), None


def get_purchase_payment_account(mode, supplier):
    if mode == Purchase.CASH:
        return get_account('Cash', ChartOfAccount.ASSET)
    if mode == Purchase.BANK:
        return get_account('Bank', ChartOfAccount.ASSET)
    return supplier


def save_purchase_journal(purchase):
    purchase_account = get_account('Purchases', ChartOfAccount.EXPENSE)
    gst_input_account = get_account('GST Input', ChartOfAccount.ASSET)
    round_off_account = get_account('Round Off', ChartOfAccount.INCOME)
    payment_account = get_purchase_payment_account(purchase.mode, purchase.supplier)

    if payment_account is None:
        raise ValueError('Supplier is required for purchase voucher')

    if purchase.journal:
        journal = purchase.journal
        journal.date = purchase.date
        journal.voucher_no = purchase.voucher_no
        journal.narration = purchase.narration
        journal.save()
        journal.lines.all().delete()
    else:
        journal = Journal.objects.create(
            date=purchase.date,
            voucher_no=purchase.voucher_no,
            narration=purchase.narration,
        )
        purchase.journal = journal
        purchase.save(update_fields=['journal'])

    JournalLine.objects.create(
        journal=journal,
        account=purchase_account,
        debit=purchase.taxable_amount,
        credit=0,
    )
    if purchase.gst_amount > 0:
        JournalLine.objects.create(
            journal=journal,
            account=gst_input_account,
            debit=purchase.gst_amount,
            credit=0,
        )
    if purchase.round_off_amount < 0:
        JournalLine.objects.create(
            journal=journal,
            account=round_off_account,
            debit=abs(purchase.round_off_amount),
            credit=0,
        )
    if purchase.round_off_amount > 0:
        JournalLine.objects.create(
            journal=journal,
            account=round_off_account,
            debit=0,
            credit=purchase.round_off_amount,
        )
    JournalLine.objects.create(
        journal=journal,
        account=payment_account,
        debit=0,
        credit=purchase.total_amount,
    )


def save_purchase_from_request(data, purchase=None):
    date = get_data_value(data, 'date', 'Date')
    parsed_date = parse_date_value(date)
    if parsed_date is None:
        return None, 'Date must be in YYYY-MM-DD, DD/MM/YYYY, DD-MM-YYYY, or YYYY/MM/DD format'

    voucher_no = get_data_value(data, 'voucher_no', 'voucherNo', 'Voucher No.')
    if not voucher_no:
        return None, 'Voucher No. is required'

    mode = normalize_purchase_mode(get_data_value(data, 'mode', 'payment_mode', 'paymentMode', default=Purchase.CASH))
    if mode is None:
        return None, 'Mode must be Cash, Bank, Credit, or Supplier'

    supplier_id = extract_id(get_data_value(
        data,
        'supplier_id',
        'supplierId',
        'supplier',
        'party_id',
        'partyId',
        'party',
        'account_id',
        'accountId',
    ))
    if not supplier_id:
        return None, 'Supplier is required'

    try:
        supplier = ChartOfAccount.objects.get(id=supplier_id)
    except ChartOfAccount.DoesNotExist:
        return None, f'Supplier id {supplier_id} does not exist'

    gst_applicable = parse_bool(get_data_value(data, 'gst_applicable', 'gstApplicable', default=True))
    prepared, error = prepare_purchase_items(get_data_value(data, 'items', 'lines', default=[]), gst_applicable)
    if error:
        return None, error

    round_off_amount = parse_amount(get_data_value(data, 'round_off_amount', 'roundOffAmount', default=0))
    if round_off_amount is None:
        return None, 'Round off amount must be a valid number'

    total_amount = money(prepared['taxable_amount'] + prepared['gst_amount'] - round_off_amount)
    if total_amount < 0:
        return None, 'Total amount cannot be negative'

    debit = parse_amount(get_data_value(data, 'debit', 'Debit', default=total_amount))
    credit = parse_amount(get_data_value(data, 'credit', 'Credit', default=total_amount))
    if debit is None or credit is None:
        return None, 'Debit and credit must be valid numbers'

    debit = money(debit)
    credit = money(credit)
    if debit != credit:
        return None, 'Debit and credit must be equal for purchase voucher'

    try:
        with transaction.atomic():
            if purchase is None:
                purchase = Purchase.objects.create(
                    date=parsed_date,
                    voucher_no=voucher_no,
                    narration=get_data_value(data, 'narration', 'Narration', default=''),
                    supplier=supplier,
                    mode=mode,
                    gst_applicable=gst_applicable,
                    taxable_amount=prepared['taxable_amount'],
                    gst_amount=prepared['gst_amount'],
                    round_off_amount=money(round_off_amount),
                    round_off_reason=get_data_value(data, 'round_off_reason', 'roundOffReason', default=''),
                    total_amount=total_amount,
                    debit=debit,
                    credit=credit,
                )
            else:
                purchase.date = parsed_date
                purchase.voucher_no = voucher_no
                purchase.narration = get_data_value(data, 'narration', 'Narration', default='')
                purchase.supplier = supplier
                purchase.mode = mode
                purchase.gst_applicable = gst_applicable
                purchase.taxable_amount = prepared['taxable_amount']
                purchase.gst_amount = prepared['gst_amount']
                purchase.round_off_amount = money(round_off_amount)
                purchase.round_off_reason = get_data_value(data, 'round_off_reason', 'roundOffReason', default='')
                purchase.total_amount = total_amount
                purchase.debit = debit
                purchase.credit = credit
                purchase.save()
                purchase.items.all().delete()

            for item in prepared['items']:
                PurchaseItem.objects.create(purchase=purchase, **item)

            save_purchase_journal(purchase)
    except Exception as exc:
        return None, str(exc)

    return (
        Purchase.objects.select_related('supplier', 'journal')
        .prefetch_related('items', 'journal__lines__account')
        .get(id=purchase.id)
    ), None


def get_sales_return_payment_account(mode, customer):
    if mode == SalesReturn.CASH:
        return get_account('Cash', ChartOfAccount.ASSET)
    if mode == SalesReturn.BANK:
        return get_account('Bank', ChartOfAccount.ASSET)
    return customer


def save_sales_return_journal(sales_return):
    sales_return_account = get_account('Sales Return', ChartOfAccount.INCOME)
    gst_output_account = get_account('GST Output', ChartOfAccount.LIABILITY)
    round_off_account = get_account('Round Off', ChartOfAccount.INCOME)
    payment_account = get_sales_return_payment_account(sales_return.mode, sales_return.customer)

    if payment_account is None:
        raise ValueError('Customer is required when mode is Credit')

    if sales_return.journal:
        journal = sales_return.journal
        journal.date = sales_return.date
        journal.voucher_no = sales_return.voucher_no
        journal.narration = sales_return.narration
        journal.save()
        journal.lines.all().delete()
    else:
        journal = Journal.objects.create(
            date=sales_return.date,
            voucher_no=sales_return.voucher_no,
            narration=sales_return.narration,
        )
        sales_return.journal = journal
        sales_return.save(update_fields=['journal'])

    JournalLine.objects.create(
        journal=journal,
        account=sales_return_account,
        debit=sales_return.taxable_amount,
        credit=0,
    )
    if sales_return.gst_amount > 0:
        JournalLine.objects.create(
            journal=journal,
            account=gst_output_account,
            debit=sales_return.gst_amount,
            credit=0,
        )
    if sales_return.round_off_amount < 0:
        JournalLine.objects.create(
            journal=journal,
            account=round_off_account,
            debit=abs(sales_return.round_off_amount),
            credit=0,
        )
    if sales_return.round_off_amount > 0:
        JournalLine.objects.create(
            journal=journal,
            account=round_off_account,
            debit=0,
            credit=sales_return.round_off_amount,
        )
    JournalLine.objects.create(
        journal=journal,
        account=payment_account,
        debit=0,
        credit=sales_return.total_amount,
    )


def save_sales_return_from_request(data, sales_return=None):
    date = get_data_value(data, 'date', 'Date')
    parsed_date = parse_date_value(date)
    if parsed_date is None:
        return None, 'Date must be in YYYY-MM-DD, DD/MM/YYYY, DD-MM-YYYY, or YYYY/MM/DD format'

    voucher_no = get_data_value(data, 'voucher_no', 'voucherNo', 'Voucher No.')
    if not voucher_no:
        return None, 'Voucher No. is required'

    mode = normalize_sales_return_mode(get_data_value(data, 'mode', 'payment_mode', 'paymentMode', default=SalesReturn.CASH))
    if mode is None:
        return None, 'Mode must be Cash, Bank, Credit, or Customer'

    customer = None
    customer_id = extract_id(get_data_value(
        data,
        'customer_id',
        'customerId',
        'customer',
        'party_id',
        'partyId',
        'party',
        'account_id',
        'accountId',
    ))
    if customer_id:
        try:
            customer = ChartOfAccount.objects.get(id=customer_id)
        except ChartOfAccount.DoesNotExist:
            return None, f'Customer id {customer_id} does not exist'

    if mode == SalesReturn.CREDIT and customer is None:
        return None, 'Customer is required when mode is Credit'

    gst_applicable = parse_bool(get_data_value(data, 'gst_applicable', 'gstApplicable', default=True))
    prepared, error = prepare_sales_return_items(get_data_value(data, 'items', 'lines', default=[]), gst_applicable)
    if error:
        return None, error

    round_off_amount = parse_amount(get_data_value(data, 'round_off_amount', 'roundOffAmount', default=0))
    if round_off_amount is None:
        return None, 'Round off amount must be a valid number'

    total_amount = money(prepared['taxable_amount'] + prepared['gst_amount'] - round_off_amount)
    if total_amount < 0:
        return None, 'Total amount cannot be negative'

    debit = parse_amount(get_data_value(data, 'debit', 'Debit', default=total_amount))
    credit = parse_amount(get_data_value(data, 'credit', 'Credit', default=total_amount))
    if debit is None or credit is None:
        return None, 'Debit and credit must be valid numbers'

    debit = money(debit)
    credit = money(credit)
    if debit != credit:
        return None, 'Debit and credit must be equal for sales return voucher'

    try:
        with transaction.atomic():
            if sales_return is None:
                sales_return = SalesReturn.objects.create(
                    date=parsed_date,
                    voucher_no=voucher_no,
                    narration=get_data_value(data, 'narration', 'Narration', default=''),
                    customer=customer,
                    mode=mode,
                    gst_applicable=gst_applicable,
                    taxable_amount=prepared['taxable_amount'],
                    gst_amount=prepared['gst_amount'],
                    round_off_amount=money(round_off_amount),
                    round_off_reason=get_data_value(data, 'round_off_reason', 'roundOffReason', default=''),
                    total_amount=total_amount,
                    debit=debit,
                    credit=credit,
                )
            else:
                sales_return.date = parsed_date
                sales_return.voucher_no = voucher_no
                sales_return.narration = get_data_value(data, 'narration', 'Narration', default='')
                sales_return.customer = customer
                sales_return.mode = mode
                sales_return.gst_applicable = gst_applicable
                sales_return.taxable_amount = prepared['taxable_amount']
                sales_return.gst_amount = prepared['gst_amount']
                sales_return.round_off_amount = money(round_off_amount)
                sales_return.round_off_reason = get_data_value(data, 'round_off_reason', 'roundOffReason', default='')
                sales_return.total_amount = total_amount
                sales_return.debit = debit
                sales_return.credit = credit
                sales_return.save()
                sales_return.items.all().delete()

            for item in prepared['items']:
                SalesReturnItem.objects.create(sales_return=sales_return, **item)

            save_sales_return_journal(sales_return)
    except Exception as exc:
        return None, str(exc)

    return (
        SalesReturn.objects.select_related('customer', 'journal')
        .prefetch_related('items', 'journal__lines__account')
        .get(id=sales_return.id)
    ), None


def get_purchase_return_payment_account(mode, supplier):
    if mode == PurchaseReturn.CASH:
        return get_account('Cash', ChartOfAccount.ASSET)
    if mode == PurchaseReturn.BANK:
        return get_account('Bank', ChartOfAccount.ASSET)
    return supplier


def save_purchase_return_journal(purchase_return):
    purchase_return_account = get_account('Purchase Return', ChartOfAccount.EXPENSE)
    gst_input_account = get_account('GST Input', ChartOfAccount.ASSET)
    round_off_account = get_account('Round Off', ChartOfAccount.INCOME)
    payment_account = get_purchase_return_payment_account(purchase_return.mode, purchase_return.supplier)

    if payment_account is None:
        raise ValueError('Supplier is required for purchase return voucher')

    if purchase_return.journal:
        journal = purchase_return.journal
        journal.date = purchase_return.date
        journal.voucher_no = purchase_return.voucher_no
        journal.narration = purchase_return.narration
        journal.save()
        journal.lines.all().delete()
    else:
        journal = Journal.objects.create(
            date=purchase_return.date,
            voucher_no=purchase_return.voucher_no,
            narration=purchase_return.narration,
        )
        purchase_return.journal = journal
        purchase_return.save(update_fields=['journal'])

    JournalLine.objects.create(
        journal=journal,
        account=payment_account,
        debit=purchase_return.total_amount,
        credit=0,
    )
    if purchase_return.round_off_amount > 0:
        JournalLine.objects.create(
            journal=journal,
            account=round_off_account,
            debit=purchase_return.round_off_amount,
            credit=0,
        )
    JournalLine.objects.create(
        journal=journal,
        account=purchase_return_account,
        debit=0,
        credit=purchase_return.taxable_amount,
    )
    if purchase_return.gst_amount > 0:
        JournalLine.objects.create(
            journal=journal,
            account=gst_input_account,
            debit=0,
            credit=purchase_return.gst_amount,
        )
    if purchase_return.round_off_amount < 0:
        JournalLine.objects.create(
            journal=journal,
            account=round_off_account,
            debit=0,
            credit=abs(purchase_return.round_off_amount),
        )


def save_purchase_return_from_request(data, purchase_return=None):
    date = get_data_value(data, 'date', 'Date')
    parsed_date = parse_date_value(date)
    if parsed_date is None:
        return None, 'Date must be in YYYY-MM-DD, DD/MM/YYYY, DD-MM-YYYY, or YYYY/MM/DD format'

    voucher_no = get_data_value(data, 'voucher_no', 'voucherNo', 'Voucher No.')
    if not voucher_no:
        return None, 'Voucher No. is required'

    mode = normalize_purchase_return_mode(get_data_value(data, 'mode', 'payment_mode', 'paymentMode', default=PurchaseReturn.CASH))
    if mode is None:
        return None, 'Mode must be Cash, Bank, Credit, or Supplier'

    supplier_id = extract_id(get_data_value(
        data,
        'supplier_id',
        'supplierId',
        'supplier',
        'party_id',
        'partyId',
        'party',
        'account_id',
        'accountId',
    ))
    if not supplier_id:
        return None, 'Supplier is required'

    try:
        supplier = ChartOfAccount.objects.get(id=supplier_id)
    except ChartOfAccount.DoesNotExist:
        return None, f'Supplier id {supplier_id} does not exist'

    gst_applicable = parse_bool(get_data_value(data, 'gst_applicable', 'gstApplicable', default=True))
    prepared, error = prepare_purchase_return_items(get_data_value(data, 'items', 'lines', default=[]), gst_applicable)
    if error:
        return None, error

    round_off_amount = parse_amount(get_data_value(data, 'round_off_amount', 'roundOffAmount', default=0))
    if round_off_amount is None:
        return None, 'Round off amount must be a valid number'

    total_amount = money(prepared['taxable_amount'] + prepared['gst_amount'] - round_off_amount)
    if total_amount < 0:
        return None, 'Total amount cannot be negative'

    debit = parse_amount(get_data_value(data, 'debit', 'Debit', default=total_amount))
    credit = parse_amount(get_data_value(data, 'credit', 'Credit', default=total_amount))
    if debit is None or credit is None:
        return None, 'Debit and credit must be valid numbers'

    debit = money(debit)
    credit = money(credit)
    if debit != credit:
        return None, 'Debit and credit must be equal for purchase return voucher'

    try:
        with transaction.atomic():
            if purchase_return is None:
                purchase_return = PurchaseReturn.objects.create(
                    date=parsed_date,
                    voucher_no=voucher_no,
                    narration=get_data_value(data, 'narration', 'Narration', default=''),
                    supplier=supplier,
                    mode=mode,
                    gst_applicable=gst_applicable,
                    taxable_amount=prepared['taxable_amount'],
                    gst_amount=prepared['gst_amount'],
                    round_off_amount=money(round_off_amount),
                    round_off_reason=get_data_value(data, 'round_off_reason', 'roundOffReason', default=''),
                    total_amount=total_amount,
                    debit=debit,
                    credit=credit,
                )
            else:
                purchase_return.date = parsed_date
                purchase_return.voucher_no = voucher_no
                purchase_return.narration = get_data_value(data, 'narration', 'Narration', default='')
                purchase_return.supplier = supplier
                purchase_return.mode = mode
                purchase_return.gst_applicable = gst_applicable
                purchase_return.taxable_amount = prepared['taxable_amount']
                purchase_return.gst_amount = prepared['gst_amount']
                purchase_return.round_off_amount = money(round_off_amount)
                purchase_return.round_off_reason = get_data_value(data, 'round_off_reason', 'roundOffReason', default='')
                purchase_return.total_amount = total_amount
                purchase_return.debit = debit
                purchase_return.credit = credit
                purchase_return.save()
                purchase_return.items.all().delete()

            for item in prepared['items']:
                PurchaseReturnItem.objects.create(purchase_return=purchase_return, **item)

            save_purchase_return_journal(purchase_return)
    except Exception as exc:
        return None, str(exc)

    return (
        PurchaseReturn.objects.select_related('supplier', 'journal')
        .prefetch_related('items', 'journal__lines__account')
        .get(id=purchase_return.id)
    ), None


def get_receipt_payment_account(mode):
    if mode == Receipt.BANK:
        return get_account('Bank', ChartOfAccount.ASSET)
    return get_account('Cash', ChartOfAccount.ASSET)


def save_receipt_journal(receipt):
    payment_account = get_receipt_payment_account(receipt.mode)

    if receipt.journal:
        journal = receipt.journal
        journal.date = receipt.date
        journal.voucher_no = receipt.voucher_no
        journal.narration = receipt.narration
        journal.save()
        journal.lines.all().delete()
    else:
        journal = Journal.objects.create(
            date=receipt.date,
            voucher_no=receipt.voucher_no,
            narration=receipt.narration,
        )
        receipt.journal = journal
        receipt.save(update_fields=['journal'])

    JournalLine.objects.create(
        journal=journal,
        account=payment_account,
        debit=receipt.amount,
        credit=0,
    )
    JournalLine.objects.create(
        journal=journal,
        account=receipt.customer,
        debit=0,
        credit=receipt.amount,
    )


def save_receipt_from_request(data, receipt=None):
    date = get_data_value(data, 'date', 'Date')
    parsed_date = parse_date_value(date)
    if parsed_date is None:
        return None, 'Date must be in YYYY-MM-DD, DD/MM/YYYY, DD-MM-YYYY, or YYYY/MM/DD format'

    voucher_no = get_data_value(data, 'voucher_no', 'voucherNo', 'Voucher No.')
    if not voucher_no:
        return None, 'Voucher No. is required'

    customer_value = get_data_value(
        data,
        'customer_id',
        'customerId',
        'customer',
        'customerName',
        'party_id',
        'partyId',
        'party',
        'partyName',
        'account_id',
        'accountId',
    )
    customer_id = extract_id(customer_value)
    customer_name = extract_name(customer_value)
    if not customer_id:
        customer_name = customer_name or get_data_value(data, 'customer_name', 'customerName', 'party_name', 'partyName')
        if not customer_name:
            return None, 'Customer is required'

    try:
        if customer_id:
            customer = ChartOfAccount.objects.get(id=customer_id)
        else:
            customer, created = ChartOfAccount.objects.get_or_create(
                name=customer_name,
                defaults={
                    'group': ChartOfAccount.ASSET,
                    'is_party': True,
                },
            )
    except ChartOfAccount.DoesNotExist:
        return None, f'Customer id {customer_id} does not exist'

    mode = normalize_receipt_mode(get_data_value(data, 'mode', 'payment_mode', 'paymentMode', default=Receipt.CASH))
    if mode is None:
        return None, 'Mode must be Cash or Bank / Cheque'

    amount = parse_amount(get_data_value(
        data,
        'amount',
        'Amount',
        'amountRs',
        'amountInr',
        'receiptAmount',
        'receivedAmount',
    ))
    if amount is None or amount <= 0:
        return None, 'Amount must be a positive number'

    amount = money(amount)
    debit = parse_amount(get_data_value(data, 'debit', 'Debit', default=amount))
    credit = parse_amount(get_data_value(data, 'credit', 'Credit', default=amount))
    if debit is None or credit is None:
        return None, 'Debit and credit must be valid numbers'

    debit = money(debit)
    credit = money(credit)
    if debit != credit:
        return None, 'Debit and credit must be equal for receipt voucher'

    try:
        with transaction.atomic():
            if receipt is None:
                receipt = Receipt.objects.create(
                    date=parsed_date,
                    voucher_no=voucher_no,
                    narration=get_data_value(data, 'narration', 'Narration', default=''),
                    customer=customer,
                    mode=mode,
                    amount=amount,
                    debit=debit,
                    credit=credit,
                )
            else:
                receipt.date = parsed_date
                receipt.voucher_no = voucher_no
                receipt.narration = get_data_value(data, 'narration', 'Narration', default='')
                receipt.customer = customer
                receipt.mode = mode
                receipt.amount = amount
                receipt.debit = debit
                receipt.credit = credit
                receipt.save()

            save_receipt_journal(receipt)
    except Exception as exc:
        return None, str(exc)

    return (
        Receipt.objects.select_related('customer', 'journal')
        .prefetch_related('journal__lines__account')
        .get(id=receipt.id)
    ), None


def get_payment_mode_account(mode):
    if mode == Payment.BANK:
        return get_account('Bank', ChartOfAccount.ASSET)
    return get_account('Cash', ChartOfAccount.ASSET)


def save_payment_journal(payment):
    payment_account = get_payment_mode_account(payment.mode)

    if payment.journal:
        journal = payment.journal
        journal.date = payment.date
        journal.voucher_no = payment.voucher_no
        journal.narration = payment.narration
        journal.save()
        journal.lines.all().delete()
    else:
        journal = Journal.objects.create(
            date=payment.date,
            voucher_no=payment.voucher_no,
            narration=payment.narration,
        )
        payment.journal = journal
        payment.save(update_fields=['journal'])

    JournalLine.objects.create(
        journal=journal,
        account=payment.supplier,
        debit=payment.amount,
        credit=0,
    )
    JournalLine.objects.create(
        journal=journal,
        account=payment_account,
        debit=0,
        credit=payment.amount,
    )


def save_payment_from_request(data, payment=None):
    date = get_data_value(data, 'date', 'Date')
    parsed_date = parse_date_value(date)
    if parsed_date is None:
        return None, 'Date must be in YYYY-MM-DD, DD/MM/YYYY, DD-MM-YYYY, or YYYY/MM/DD format'

    voucher_no = get_data_value(data, 'voucher_no', 'voucherNo', 'Voucher No.')
    if not voucher_no:
        return None, 'Voucher No. is required'

    supplier_id = extract_id(get_data_value(
        data,
        'supplier_id',
        'supplierId',
        'supplier',
        'party_id',
        'partyId',
        'party',
        'account_id',
        'accountId',
    ))
    if not supplier_id:
        return None, 'Supplier is required'

    try:
        supplier = ChartOfAccount.objects.get(id=supplier_id)
    except ChartOfAccount.DoesNotExist:
        return None, f'Supplier id {supplier_id} does not exist'

    mode = normalize_payment_mode(get_data_value(data, 'mode', 'payment_mode', 'paymentMode', default=Payment.CASH))
    if mode is None:
        return None, 'Mode must be Cash or Bank / Cheque'

    amount = parse_amount(get_data_value(data, 'amount', 'Amount'))
    if amount is None or amount <= 0:
        return None, 'Amount must be a positive number'

    amount = money(amount)
    debit = parse_amount(get_data_value(data, 'debit', 'Debit', default=amount))
    credit = parse_amount(get_data_value(data, 'credit', 'Credit', default=amount))
    if debit is None or credit is None:
        return None, 'Debit and credit must be valid numbers'

    debit = money(debit)
    credit = money(credit)
    if debit != credit:
        return None, 'Debit and credit must be equal for payment voucher'

    try:
        with transaction.atomic():
            if payment is None:
                payment = Payment.objects.create(
                    date=parsed_date,
                    voucher_no=voucher_no,
                    narration=get_data_value(data, 'narration', 'Narration', default=''),
                    supplier=supplier,
                    mode=mode,
                    amount=amount,
                    debit=debit,
                    credit=credit,
                )
            else:
                payment.date = parsed_date
                payment.voucher_no = voucher_no
                payment.narration = get_data_value(data, 'narration', 'Narration', default='')
                payment.supplier = supplier
                payment.mode = mode
                payment.amount = amount
                payment.debit = debit
                payment.credit = credit
                payment.save()

            save_payment_journal(payment)
    except Exception as exc:
        return None, str(exc)

    return (
        Payment.objects.select_related('supplier', 'journal')
        .prefetch_related('journal__lines__account')
        .get(id=payment.id)
    ), None


def get_expense_payment_account(mode):
    if mode == Expense.BANK:
        return get_account('Bank', ChartOfAccount.ASSET)
    return get_account('Cash', ChartOfAccount.ASSET)


def save_expense_journal(expense):
    payment_account = get_expense_payment_account(expense.mode)

    if expense.journal:
        journal = expense.journal
        journal.date = expense.date
        journal.voucher_no = expense.voucher_no
        journal.narration = expense.narration
        journal.save()
        journal.lines.all().delete()
    else:
        journal = Journal.objects.create(
            date=expense.date,
            voucher_no=expense.voucher_no,
            narration=expense.narration,
        )
        expense.journal = journal
        expense.save(update_fields=['journal'])

    JournalLine.objects.create(
        journal=journal,
        account=expense.expense_head,
        debit=expense.amount,
        credit=0,
    )
    JournalLine.objects.create(
        journal=journal,
        account=payment_account,
        debit=0,
        credit=expense.amount,
    )


def save_expense_from_request(data, expense=None):
    date = get_data_value(data, 'date', 'Date')
    parsed_date = parse_date_value(date)
    if parsed_date is None:
        return None, 'Date must be in YYYY-MM-DD, DD/MM/YYYY, DD-MM-YYYY, or YYYY/MM/DD format'

    voucher_no = get_data_value(data, 'voucher_no', 'voucherNo', 'Voucher No.')
    if not voucher_no:
        return None, 'Voucher No. is required'

    expense_head_id = extract_id(get_data_value(
        data,
        'expense_head_id',
        'expenseHeadId',
        'expense_head',
        'expenseHead',
        'account_id',
        'accountId',
        'account',
        'head_id',
        'headId',
        'head',
    ))
    if not expense_head_id:
        return None, 'Expense head is required'

    try:
        expense_head = ChartOfAccount.objects.get(id=expense_head_id)
    except ChartOfAccount.DoesNotExist:
        return None, f'Expense head id {expense_head_id} does not exist'

    mode = normalize_expense_mode(get_data_value(data, 'mode', 'payment_mode', 'paymentMode', default=Expense.CASH))
    if mode is None:
        return None, 'Mode must be Cash or Bank / Cheque'

    amount = parse_amount(get_data_value(data, 'amount', 'Amount'))
    if amount is None or amount <= 0:
        return None, 'Amount must be a positive number'

    amount = money(amount)
    debit = parse_amount(get_data_value(data, 'debit', 'Debit', default=amount))
    credit = parse_amount(get_data_value(data, 'credit', 'Credit', default=amount))
    if debit is None or credit is None:
        return None, 'Debit and credit must be valid numbers'

    debit = money(debit)
    credit = money(credit)
    if debit != credit:
        return None, 'Debit and credit must be equal for expense voucher'

    try:
        with transaction.atomic():
            if expense is None:
                expense = Expense.objects.create(
                    date=parsed_date,
                    voucher_no=voucher_no,
                    narration=get_data_value(data, 'narration', 'Narration', default=''),
                    expense_head=expense_head,
                    mode=mode,
                    amount=amount,
                    debit=debit,
                    credit=credit,
                )
            else:
                expense.date = parsed_date
                expense.voucher_no = voucher_no
                expense.narration = get_data_value(data, 'narration', 'Narration', default='')
                expense.expense_head = expense_head
                expense.mode = mode
                expense.amount = amount
                expense.debit = debit
                expense.credit = credit
                expense.save()

            save_expense_journal(expense)
    except Exception as exc:
        return None, str(exc)

    return (
        Expense.objects.select_related('expense_head', 'journal')
        .prefetch_related('journal__lines__account')
        .get(id=expense.id)
    ), None


def save_contra_journal(contra):
    cash_account = get_account('Cash', ChartOfAccount.ASSET)
    bank_account = get_account('Bank', ChartOfAccount.ASSET)
    round_off_account = get_account('Round Off', ChartOfAccount.INCOME)

    if contra.direction == Contra.BANK_TO_CASH:
        debit_account = cash_account
        credit_account = bank_account
    else:
        debit_account = bank_account
        credit_account = cash_account

    if contra.journal:
        journal = contra.journal
        journal.date = contra.date
        journal.voucher_no = contra.voucher_no
        journal.narration = contra.narration
        journal.save()
        journal.lines.all().delete()
    else:
        journal = Journal.objects.create(
            date=contra.date,
            voucher_no=contra.voucher_no,
            narration=contra.narration,
        )
        contra.journal = journal
        contra.save(update_fields=['journal'])

    debit_amount = contra.amount
    credit_amount = contra.amount
    if contra.round_off_amount < 0:
        debit_amount += abs(contra.round_off_amount)
    if contra.round_off_amount > 0:
        credit_amount += contra.round_off_amount

    JournalLine.objects.create(
        journal=journal,
        account=debit_account,
        debit=debit_amount,
        credit=0,
    )
    if contra.round_off_amount > 0:
        JournalLine.objects.create(
            journal=journal,
            account=round_off_account,
            debit=contra.round_off_amount,
            credit=0,
        )
        JournalLine.objects.create(
            journal=journal,
            account=credit_account,
            debit=0,
            credit=credit_amount,
        )
    if contra.round_off_amount < 0:
        JournalLine.objects.create(
            journal=journal,
            account=round_off_account,
            debit=0,
            credit=abs(contra.round_off_amount),
        )


def save_contra_from_request(data, contra=None):
    date = get_data_value(data, 'date', 'Date')
    parsed_date = parse_date_value(date)
    if parsed_date is None:
        return None, 'Date must be in YYYY-MM-DD, DD/MM/YYYY, DD-MM-YYYY, or YYYY/MM/DD format'

    voucher_no = get_data_value(data, 'voucher_no', 'voucherNo', 'Voucher No.')
    if not voucher_no:
        return None, 'Voucher No. is required'

    direction = normalize_contra_direction(get_data_value(data, 'direction', 'Direction', default=Contra.BANK_TO_CASH))
    if direction is None:
        return None, 'Direction must be Bank to Cash or Cash to Bank'

    amount = parse_amount(get_data_value(data, 'amount', 'Amount'))
    if amount is None or amount <= 0:
        return None, 'Amount must be a positive number'

    round_off_amount = parse_amount(get_data_value(data, 'round_off_amount', 'roundOffAmount', default=0))
    if round_off_amount is None:
        return None, 'Round off amount must be a valid number'

    amount = money(amount)
    round_off_amount = money(round_off_amount)
    total_amount = amount

    expected_total = money(amount + abs(round_off_amount))
    debit = parse_amount(get_data_value(data, 'debit', 'Debit', default=expected_total))
    credit = parse_amount(get_data_value(data, 'credit', 'Credit', default=expected_total))
    if debit is None or credit is None:
        return None, 'Debit and credit must be valid numbers'

    debit = money(debit)
    credit = money(credit)
    if debit != credit:
        return None, 'Debit and credit must be equal for contra voucher'
    if debit != expected_total or credit != expected_total:
        return None, 'Debit and credit must match contra amount and round off'

    try:
        with transaction.atomic():
            if contra is None:
                contra = Contra.objects.create(
                    date=parsed_date,
                    voucher_no=voucher_no,
                    narration=get_data_value(data, 'narration', 'Narration', default=''),
                    direction=direction,
                    amount=amount,
                    round_off_amount=round_off_amount,
                    round_off_reason=get_data_value(data, 'round_off_reason', 'roundOffReason', default=''),
                    total_amount=total_amount,
                    debit=debit,
                    credit=credit,
                )
            else:
                contra.date = parsed_date
                contra.voucher_no = voucher_no
                contra.narration = get_data_value(data, 'narration', 'Narration', default='')
                contra.direction = direction
                contra.amount = amount
                contra.round_off_amount = round_off_amount
                contra.round_off_reason = get_data_value(data, 'round_off_reason', 'roundOffReason', default='')
                contra.total_amount = total_amount
                contra.debit = debit
                contra.credit = credit
                contra.save()

            save_contra_journal(contra)
    except Exception as exc:
        return None, str(exc)

    return (
        Contra.objects.select_related('journal')
        .prefetch_related('journal__lines__account')
        .get(id=contra.id)
    ), None


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


@api_view(['GET', 'POST'])
def sales(request):
    if request.method == 'GET':
        sale_list = (
            Sale.objects.select_related('customer', 'journal')
            .prefetch_related('items', 'journal__lines__account')
            .all()
        )
        return Response({
            'status': True,
            'data': [serialize_sale(sale) for sale in sale_list],
        })

    sale, error = save_sale_from_request(request.data)
    if error:
        return Response({
            'status': False,
            'message': error,
        }, status=status.HTTP_400_BAD_REQUEST)

    return Response({
        'status': True,
        'message': 'Sale created successfully',
        'data': serialize_sale(sale),
    }, status=status.HTTP_201_CREATED)


@api_view(['GET', 'POST'])
def purchases(request):
    if request.method == 'GET':
        purchase_list = (
            Purchase.objects.select_related('supplier', 'journal')
            .prefetch_related('items', 'journal__lines__account')
            .all()
        )
        return Response({
            'status': True,
            'data': [serialize_purchase(purchase) for purchase in purchase_list],
        })

    purchase, error = save_purchase_from_request(request.data)
    if error:
        return Response({
            'status': False,
            'message': error,
        }, status=status.HTTP_400_BAD_REQUEST)

    return Response({
        'status': True,
        'message': 'Purchase created successfully',
        'data': serialize_purchase(purchase),
    }, status=status.HTTP_201_CREATED)


@api_view(['GET', 'POST'])
def sales_returns(request):
    if request.method == 'GET':
        sales_return_list = (
            SalesReturn.objects.select_related('customer', 'journal')
            .prefetch_related('items', 'journal__lines__account')
            .all()
        )
        return Response({
            'status': True,
            'data': [serialize_sales_return(sales_return) for sales_return in sales_return_list],
        })

    sales_return, error = save_sales_return_from_request(request.data)
    if error:
        return Response({
            'status': False,
            'message': error,
        }, status=status.HTTP_400_BAD_REQUEST)

    return Response({
        'status': True,
        'message': 'Sales return created successfully',
        'data': serialize_sales_return(sales_return),
    }, status=status.HTTP_201_CREATED)


@api_view(['GET', 'POST'])
def purchase_returns(request):
    if request.method == 'GET':
        purchase_return_list = (
            PurchaseReturn.objects.select_related('supplier', 'journal')
            .prefetch_related('items', 'journal__lines__account')
            .all()
        )
        return Response({
            'status': True,
            'data': [serialize_purchase_return(purchase_return) for purchase_return in purchase_return_list],
        })

    purchase_return, error = save_purchase_return_from_request(request.data)
    if error:
        return Response({
            'status': False,
            'message': error,
        }, status=status.HTTP_400_BAD_REQUEST)

    return Response({
        'status': True,
        'message': 'Purchase return created successfully',
        'data': serialize_purchase_return(purchase_return),
    }, status=status.HTTP_201_CREATED)


@api_view(['GET', 'POST'])
def receipts(request):
    if request.method == 'GET':
        receipt_list = (
            Receipt.objects.select_related('customer', 'journal')
            .prefetch_related('journal__lines__account')
            .all()
        )
        return Response({
            'status': True,
            'data': [serialize_receipt(receipt) for receipt in receipt_list],
        })

    receipt, error = save_receipt_from_request(request.data)
    if error:
        return Response({
            'status': False,
            'message': error,
        }, status=status.HTTP_400_BAD_REQUEST)

    return Response({
        'status': True,
        'message': 'Receipt created successfully',
        'data': serialize_receipt(receipt),
    }, status=status.HTTP_201_CREATED)


@api_view(['GET', 'POST'])
def payments(request):
    if request.method == 'GET':
        payment_list = (
            Payment.objects.select_related('supplier', 'journal')
            .prefetch_related('journal__lines__account')
            .all()
        )
        return Response({
            'status': True,
            'data': [serialize_payment(payment) for payment in payment_list],
        })

    payment, error = save_payment_from_request(request.data)
    if error:
        return Response({
            'status': False,
            'message': error,
        }, status=status.HTTP_400_BAD_REQUEST)

    return Response({
        'status': True,
        'message': 'Payment created successfully',
        'data': serialize_payment(payment),
    }, status=status.HTTP_201_CREATED)


@api_view(['GET', 'POST'])
def expenses(request):
    if request.method == 'GET':
        expense_list = (
            Expense.objects.select_related('expense_head', 'journal')
            .prefetch_related('journal__lines__account')
            .all()
        )
        return Response({
            'status': True,
            'data': [serialize_expense(expense) for expense in expense_list],
        })

    expense, error = save_expense_from_request(request.data)
    if error:
        return Response({
            'status': False,
            'message': error,
        }, status=status.HTTP_400_BAD_REQUEST)

    return Response({
        'status': True,
        'message': 'Expense created successfully',
        'data': serialize_expense(expense),
    }, status=status.HTTP_201_CREATED)


@api_view(['GET', 'POST'])
def contras(request):
    if request.method == 'GET':
        contra_list = (
            Contra.objects.select_related('journal')
            .prefetch_related('journal__lines__account')
            .all()
        )
        return Response({
            'status': True,
            'data': [serialize_contra(contra) for contra in contra_list],
        })

    contra, error = save_contra_from_request(request.data)
    if error:
        return Response({
            'status': False,
            'message': error,
        }, status=status.HTTP_400_BAD_REQUEST)

    return Response({
        'status': True,
        'message': 'Contra created successfully',
        'data': serialize_contra(contra),
    }, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
def sale_detail(request, sale_id):
    try:
        sale = (
            Sale.objects.select_related('customer', 'journal')
            .prefetch_related('items', 'journal__lines__account')
            .get(id=sale_id)
        )
    except Sale.DoesNotExist:
        return Response({
            'status': False,
            'message': 'Sale not found',
        }, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        return Response({
            'status': True,
            'data': serialize_sale(sale),
        })

    if request.method == 'DELETE':
        sale.delete()
        return Response({
            'status': True,
            'message': 'Sale deleted successfully',
        })

    updated_sale, error = save_sale_from_request(request.data, sale=sale)
    if error:
        return Response({
            'status': False,
            'message': error,
        }, status=status.HTTP_400_BAD_REQUEST)

    return Response({
        'status': True,
        'message': 'Sale updated successfully',
        'data': serialize_sale(updated_sale),
    })


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
def purchase_detail(request, purchase_id):
    try:
        purchase = (
            Purchase.objects.select_related('supplier', 'journal')
            .prefetch_related('items', 'journal__lines__account')
            .get(id=purchase_id)
        )
    except Purchase.DoesNotExist:
        return Response({
            'status': False,
            'message': 'Purchase not found',
        }, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        return Response({
            'status': True,
            'data': serialize_purchase(purchase),
        })

    if request.method == 'DELETE':
        purchase.delete()
        return Response({
            'status': True,
            'message': 'Purchase deleted successfully',
        })

    updated_purchase, error = save_purchase_from_request(request.data, purchase=purchase)
    if error:
        return Response({
            'status': False,
            'message': error,
        }, status=status.HTTP_400_BAD_REQUEST)

    return Response({
        'status': True,
        'message': 'Purchase updated successfully',
        'data': serialize_purchase(updated_purchase),
    })


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
def sales_return_detail(request, sales_return_id):
    try:
        sales_return = (
            SalesReturn.objects.select_related('customer', 'journal')
            .prefetch_related('items', 'journal__lines__account')
            .get(id=sales_return_id)
        )
    except SalesReturn.DoesNotExist:
        return Response({
            'status': False,
            'message': 'Sales return not found',
        }, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        return Response({
            'status': True,
            'data': serialize_sales_return(sales_return),
        })

    if request.method == 'DELETE':
        sales_return.delete()
        return Response({
            'status': True,
            'message': 'Sales return deleted successfully',
        })

    updated_sales_return, error = save_sales_return_from_request(request.data, sales_return=sales_return)
    if error:
        return Response({
            'status': False,
            'message': error,
        }, status=status.HTTP_400_BAD_REQUEST)

    return Response({
        'status': True,
        'message': 'Sales return updated successfully',
        'data': serialize_sales_return(updated_sales_return),
    })


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
def purchase_return_detail(request, purchase_return_id):
    try:
        purchase_return = (
            PurchaseReturn.objects.select_related('supplier', 'journal')
            .prefetch_related('items', 'journal__lines__account')
            .get(id=purchase_return_id)
        )
    except PurchaseReturn.DoesNotExist:
        return Response({
            'status': False,
            'message': 'Purchase return not found',
        }, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        return Response({
            'status': True,
            'data': serialize_purchase_return(purchase_return),
        })

    if request.method == 'DELETE':
        purchase_return.delete()
        return Response({
            'status': True,
            'message': 'Purchase return deleted successfully',
        })

    updated_purchase_return, error = save_purchase_return_from_request(request.data, purchase_return=purchase_return)
    if error:
        return Response({
            'status': False,
            'message': error,
        }, status=status.HTTP_400_BAD_REQUEST)

    return Response({
        'status': True,
        'message': 'Purchase return updated successfully',
        'data': serialize_purchase_return(updated_purchase_return),
    })


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
def receipt_detail(request, receipt_id):
    try:
        receipt = (
            Receipt.objects.select_related('customer', 'journal')
            .prefetch_related('journal__lines__account')
            .get(id=receipt_id)
        )
    except Receipt.DoesNotExist:
        return Response({
            'status': False,
            'message': 'Receipt not found',
        }, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        return Response({
            'status': True,
            'data': serialize_receipt(receipt),
        })

    if request.method == 'DELETE':
        receipt.delete()
        return Response({
            'status': True,
            'message': 'Receipt deleted successfully',
        })

    updated_receipt, error = save_receipt_from_request(request.data, receipt=receipt)
    if error:
        return Response({
            'status': False,
            'message': error,
        }, status=status.HTTP_400_BAD_REQUEST)

    return Response({
        'status': True,
        'message': 'Receipt updated successfully',
        'data': serialize_receipt(updated_receipt),
    })


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
def payment_detail(request, payment_id):
    try:
        payment = (
            Payment.objects.select_related('supplier', 'journal')
            .prefetch_related('journal__lines__account')
            .get(id=payment_id)
        )
    except Payment.DoesNotExist:
        return Response({
            'status': False,
            'message': 'Payment not found',
        }, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        return Response({
            'status': True,
            'data': serialize_payment(payment),
        })

    if request.method == 'DELETE':
        payment.delete()
        return Response({
            'status': True,
            'message': 'Payment deleted successfully',
        })

    updated_payment, error = save_payment_from_request(request.data, payment=payment)
    if error:
        return Response({
            'status': False,
            'message': error,
        }, status=status.HTTP_400_BAD_REQUEST)

    return Response({
        'status': True,
        'message': 'Payment updated successfully',
        'data': serialize_payment(updated_payment),
    })


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
def expense_detail(request, expense_id):
    try:
        expense = (
            Expense.objects.select_related('expense_head', 'journal')
            .prefetch_related('journal__lines__account')
            .get(id=expense_id)
        )
    except Expense.DoesNotExist:
        return Response({
            'status': False,
            'message': 'Expense not found',
        }, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        return Response({
            'status': True,
            'data': serialize_expense(expense),
        })

    if request.method == 'DELETE':
        expense.delete()
        return Response({
            'status': True,
            'message': 'Expense deleted successfully',
        })

    updated_expense, error = save_expense_from_request(request.data, expense=expense)
    if error:
        return Response({
            'status': False,
            'message': error,
        }, status=status.HTTP_400_BAD_REQUEST)

    return Response({
        'status': True,
        'message': 'Expense updated successfully',
        'data': serialize_expense(updated_expense),
    })


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
def contra_detail(request, contra_id):
    try:
        contra = (
            Contra.objects.select_related('journal')
            .prefetch_related('journal__lines__account')
            .get(id=contra_id)
        )
    except Contra.DoesNotExist:
        return Response({
            'status': False,
            'message': 'Contra not found',
        }, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        return Response({
            'status': True,
            'data': serialize_contra(contra),
        })

    if request.method == 'DELETE':
        contra.delete()
        return Response({
            'status': True,
            'message': 'Contra deleted successfully',
        })

    updated_contra, error = save_contra_from_request(request.data, contra=contra)
    if error:
        return Response({
            'status': False,
            'message': error,
        }, status=status.HTTP_400_BAD_REQUEST)

    return Response({
        'status': True,
        'message': 'Contra updated successfully',
        'data': serialize_contra(updated_contra),
    })
