from django.contrib import messages
from django.db import models
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

from reviews.forms import ReviewForm
from reviews.models import Review
from skills.models import ExchangeRequest


@login_required
def add_review(request, user_id):
    user = get_object_or_404(User, id=user_id)

    completed_exchanges = ExchangeRequest.objects.filter(status='completed').filter(
        models.Q(sender=request.user, receiver=user) |
        models.Q(sender=user, receiver=request.user)
    )

    completed_exchanges_count = completed_exchanges.count()
    submitted_reviews_count = Review.objects.filter(reviewer=request.user, reviewed_user=user).count()

    if not completed_exchanges.exists():
        messages.error(request, 'You can only leave a review after a completed exchange with this user.')
        return redirect('profile', user_id=user.id)

    if submitted_reviews_count >= completed_exchanges_count:
        messages.error(request, 'You have already submitted all available reviews for completed exchanges with this user.')
        return redirect('profile', user_id=user.id)

    form = ReviewForm(request.POST or None)
    if form.is_valid():
        review = form.save(commit=False)
        review.reviewer = request.user
        review.reviewed_user = user
        review.save()
        messages.success(request, 'Review submitted. Thank you for your feedback!')
        return redirect('profile', user_id=user.id)
    return render(request, 'review.html', {'form': form, 'reviewed_user': user})
