from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User


class RegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']


class RoleAuthenticationForm(AuthenticationForm):
    ACCOUNT_TYPE_ADMIN = 'admin'
    ACCOUNT_TYPE_USER = 'user'
    ACCOUNT_TYPE_CHOICES = [
        (ACCOUNT_TYPE_USER, 'User account'),
        (ACCOUNT_TYPE_ADMIN, 'Admin'),
    ]

    account_type = forms.ChoiceField(
        choices=ACCOUNT_TYPE_CHOICES,
        initial=ACCOUNT_TYPE_USER,
        widget=forms.RadioSelect,
        label='Login as',
    )

    def __init__(self, request=None, *args, **kwargs):
        super().__init__(request=request, *args, **kwargs)
        self.order_fields(['account_type', 'username', 'password'])
