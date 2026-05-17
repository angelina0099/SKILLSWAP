from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render
from django.urls import reverse

from reviews.models import Review
from skills.models import Skill

from .forms import RegisterForm, RoleAuthenticationForm


def profile(request, user_id):
    user = User.objects.get(id=user_id)
    skills = Skill.objects.filter(owner=user)
    reviews = Review.objects.filter(reviewed_user=user)
    return render(request, 'profile.html', {
        'profile_user': user,
        'skills': skills,
        'reviews': reviews
    })


def register(request):
    if request.user.is_authenticated:
        return redirect('home')

    form = RegisterForm(request.POST or None)
    if form.is_valid():
        user = form.save()
        login(request, user)
        return redirect('home')

    return render(request, 'registration/register.html', {'form': form})


class RoleLoginView(LoginView):
    form_class = RoleAuthenticationForm
    template_name = 'registration/login.html'

    def form_valid(self, form):
        account_type = form.cleaned_data.get('account_type')
        user = form.get_user()

        can_manage = user.is_staff or user.is_superuser
        if account_type == RoleAuthenticationForm.ACCOUNT_TYPE_ADMIN and not can_manage:
            account_type = RoleAuthenticationForm.ACCOUNT_TYPE_USER
            messages.info(
                self.request,
                'Admin mode is reserved for management accounts. You were logged in as a user account.',
            )

        self.request.session['account_type_choice'] = account_type
        return super().form_valid(form)

    def get_success_url(self):
        redirect_to = self.get_redirect_url()
        if redirect_to:
            return redirect_to

        account_type = self.request.session.pop('account_type_choice', None)
        if account_type == RoleAuthenticationForm.ACCOUNT_TYPE_ADMIN:
            messages.success(self.request, 'Logged in as administrator.')
            return reverse('admin_dashboard')

        return reverse('home')
