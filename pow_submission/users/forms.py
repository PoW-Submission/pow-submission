import random, string
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django import forms


from .models import ADUser 


class CustomUserCreationForm(UserCreationForm):

    password1 = None 
    password2 = None 

    class Meta:
        model = ADUser 
        fields = ('email',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        user = super(forms.ModelForm, self).save(commit=False)
        user.set_password(''.join(random.choices(string.ascii_letters + string.digits + string.punctuation, k=20)))
        if commit:
            user.save()
        return user

class CustomUserChangeForm(UserChangeForm):

    class Meta:
        model = ADUser
        fields = ('email',)
