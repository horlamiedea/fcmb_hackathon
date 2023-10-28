from django.db import models
from django.contrib.auth.models import (AbstractBaseUser,
                                        BaseUserManager,
                                        PermissionsMixin,
                                        AbstractUser)
from phonenumber_field.modelfields import PhoneNumberField
from django.utils.translation import gettext_lazy as _

# Create your models here.
from rest_framework_simplejwt.tokens import RefreshToken


class CustomUserManager(BaseUserManager):

    def create_user(self, first_name, last_name, phone_number, email, password=None, *args, **kwargs):

        if not email:
            raise ValueError('User must have an email address')

        if not phone_number:
            raise ValueError("User must have a phone number")

        # if not username:
        #     raise ValueError('User must have an username')

        user = self.model(
            email=self.normalize_email(email),
            # username=username,
            first_name=first_name,
            last_name=last_name,
            # role=role,
            phone_number=phone_number,
            **kwargs
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, password=None, email=None, **kwargs):
        if password is None:
            raise TypeError('Password should not be none')

        # if not email:
        #     raise ValueError('User must have an email address')

        if not phone_number:
            raise ValueError("User must have a phone number")

        kwargs.update({'is_superuser': True,
                       'is_staff': True,
                       'is_admin': True})

        user = self.model(
            email=self.normalize_email(email),
            phone_number=phone_number,
            **kwargs
        )
        user.set_password(password)
        user.save(using=self._db)
        return user


class VerifyIDChoices(models.TextChoices):
    DRIVERS_LICENCE = ('DRIVERS_LICENCE', "driver's license")
    NIN = ('NIN', 'nin')
    VOTERS_CARD = ('VOTERS_CARD', "voter's card")


class User(AbstractBaseUser, PermissionsMixin):

    first_name = models.CharField(max_length=50, blank=True, null=True)
    last_name = models.CharField(max_length=50, blank=True, null=True)
    email = models.EmailField(_('email address'), unique=True, null=True)
    phone_number = PhoneNumberField(unique=True)
    wallet = models.DecimalField(max_digits=20, decimal_places=2, default=0.00, null=True)
    otp = models.CharField(default='0000', max_length=4)
    # location = models.PointField(null=True, blank=True, srid=4326)
    location_lat = models.FloatField(null=True, blank=True, default=0)
    location_long = models.FloatField(null=True, blank=True, default=0)
    address = models.TextField(_('home address'), null=True, blank=True)
    credit_score = models.IntegerField(default=0)
    verify_ID = models.FileField(upload_to='verifyId', null=True, blank=True)
    verify_ID_name = models.CharField(max_length=512, null=True, blank=True, choices=VerifyIDChoices.choices)
    nin = models.CharField(max_length=512, null=True, blank=True)
    bvn = models.CharField(max_length=512, null=True, blank=True)

    # required fields
    date_joined = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    is_admin = models.BooleanField(default=False)
    is_agent = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=False)

    # USERNAME_FIELD = 'email'
    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = ['email']

    objects = CustomUserManager()

    def __str__(self):
        return str(self.phone_number) + f' - {self.email}'

    # def save(self, *args, **kwargs):
    #     self.location = Point(float(self.location_long), float(self.location_lat))
    #     return super().save(*args, **kwargs)
    # TODO location

    @property
    def tokens(self):
        refresh = RefreshToken.for_user(self)
        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }


class BenificiaryContact(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='beneficiary')
    first_name = models.CharField(max_length=512, null=True, blank=True)
    last_name = models.CharField(max_length=512, null=True, blank=True)
    bvn = models.CharField(max_length=512, null=True, blank=True)
    verify_ID = models.FileField(upload_to='verifyId', null=True, blank=True)
    verify_ID_name = models.CharField(max_length=512, null=True, blank=True, choices=VerifyIDChoices.choices)


class AdvertisedLoan(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='advertised_loan', null=True)
    initial_amount = models.DecimalField(max_digits=20, decimal_places=2, null=True)
    total_amount_remaining = models.DecimalField(max_digits=20, decimal_places=2, null=True)
    interest = models.DecimalField(max_digits=20, decimal_places=2, null=True)
    period = models.IntegerField(_('number of days'))
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    times_to_pay = models.IntegerField(_('pay x times'))


class Loan(models.Model):
    advertised_loan = models.ForeignKey(AdvertisedLoan, on_delete=models.SET_NULL, related_name='loan', null=True)
    receiving_user = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='loan', null=True)
    amount = models.DecimalField(max_digits=20, decimal_places=2, null=True)
    created_at = models.DateTimeField(auto_now_add=True)


class LoanRepayment(models.Model):
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='repayment')
    amount = models.DecimalField(max_digits=20, decimal_places=2, null=True)
    date = models.DateTimeField(auto_now=True)
    is_paid = models.BooleanField(default=False)
    remaining_balance = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)


class TransactionHistoryChoices(models.TextChoices):
    WITHDRAWAL = 'WITHDRAWAL', 'withdrawal'
    DEPOSIT = 'DEPOSIT', 'deposit'
    TRANSFER = 'TRANSFER', 'transfer'
    LOAN_REPAYMENT = 'LOAN_REPAYMENT', 'loan_repayment'


class TransactionHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='transaction_history', null=True)
    agent = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='agent_transaction_history', null=True)
    title = models.CharField(max_length=512, null=True, blank=True, choices=TransactionHistoryChoices.choices)
    remaining_balance = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
