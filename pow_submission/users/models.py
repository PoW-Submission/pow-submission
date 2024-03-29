from django.db import models
from django.utils import  timezone
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.utils.translation import ugettext_lazy as _

class LowerEmailField(models.EmailField):
    def __init__(self, *args, **kwargs):
        super(LowerEmailField, self).__init__(*args, **kwargs)

    def get_prep_value(self, value):
        return str(value).lower()

class CustomUserManager(BaseUserManager):
    """
    Custom user model manager where email is the unique identifiers
    for authentication instead of usernames.
    """
    def create_user(self, email, password, **extra_fields):
        """
        Create and save a User with the given email and password.
        """
        if not email:
            raise ValueError(_('The Email must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password, **extra_fields):
        """
        Create and save a SuperUser with the given email and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        return self.create_user(email, password, **extra_fields)

class ADUser(AbstractUser):
    username = None
    email = LowerEmailField(max_length=255, unique=True)
    track = models.ForeignKey('core.Track', blank=True, null=True, on_delete=models.SET_NULL)
    advisor = models.ForeignKey('core.Faculty', blank=True, null=True, on_delete=models.SET_NULL)
    always_notify= models.BooleanField(default=False, help_text='For Education Leadership.  Will always receive email notifications and can finalize term plans.')
    is_faculty = models.BooleanField(default=False, help_text='Determines whether user can see Faculty or Student side of application.')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email

class LoginToken(models.Model):
    user = models.ForeignKey(ADUser, null=False, on_delete=models.CASCADE) 
    token = models.CharField(max_length=40, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    

class PotentialUser(models.Model):
    email = LowerEmailField(max_length=255, unique=True)
    
    def __str__(self):
        return self.email
