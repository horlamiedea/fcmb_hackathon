from django.db.models.signals import post_save, pre_save, pre_delete, post_delete
from django.dispatch import receiver
from .models import *
from decimal import Decimal
from datetime import datetime, timedelta


@receiver(post_save, sender=Loan)
def send_otp_on_create(sender, instance: Loan, created, **kwargs):
    if created:
        repayment_plans = []
        for i in range(instance.advertised_loan.times_to_pay):
            days = instance.advertised_loan.period / instance.advertised_loan.times_to_pay
            date = instance.created_at + timedelta(days=days)
            repayment_plans.append(LoanRepayment(
                loan=instance,
                amount=instance.amount/Decimal(instance.advertised_loan.times_to_pay),
                date=date
            ))
        LoanRepayment.objects.bulk_create(repayment_plans)