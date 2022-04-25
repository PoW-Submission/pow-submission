import typing

from users.models import ADUser, LoginToken
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from django.http import HttpResponse, Http404
import datetime
from datetime import timezone

UserModel = get_user_model()

class TokenLogin(ModelBackend):
    def authenticate(
            #set correct variables
        self, request=None, token=None):
        print('Start method')
        try:
            loginToken = LoginToken.objects.filter(token=token)[0]
            print(loginToken.created_at)
            
            if loginToken and ((datetime.datetime.now(timezone.utc) - datetime.timedelta(minutes=15)) < loginToken.created_at):
                return loginToken.user
        except:
            return None

        return None 

