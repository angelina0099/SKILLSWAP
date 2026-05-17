from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db import models
from django.shortcuts import get_object_or_404, render, redirect
from django.utils import timezone

from reviews.models import Review
from .forms import SkillForm
from .models import ExchangeRequest, Report, Skill


def home(request):
    skills = Skill.objects.all()
    return render(request, 'home.html', {
        'skills': skills,
        'categories': Skill.CATEGORY_CHOICES,
    })


@login_required
def add_skill(request):
    form = SkillForm(request.POST or None)
    if form.is_valid():
        skill = form.save(commit=False)
        skill.owner = request.user
        skill.save()
        messages.success(request, 'Skill added successfully. Other members can now request an exchange.')
        return redirect('home')
    return render(request, 'add_skill.html', {'form': form})


def search(request):
    query = request.GET.get('q', '').strip()
    raw_category = request.GET.get('category', '').strip().lower()
    category_aliases = {'others': 'other'}
    category = category_aliases.get(raw_category, raw_category)
    valid_categories = {value for value, _ in Skill.CATEGORY_CHOICES}
    if category and category not in valid_categories:
        category = ''
    results = None

    if 'q' in request.GET or 'category' in request.GET:
        results = Skill.objects.select_related('owner').order_by('-created')
        if query:
            results = results.filter(
                models.Q(title__icontains=query) | models.Q(description__icontains=query)
            )
        if category:
            results = results.filter(category__iexact=category)

    return render(request, 'search.html', {
        'results': results,
        'query': query,
        'selected_category': category,
        'categories': Skill.CATEGORY_CHOICES,
    })


@login_required
def request_exchange(request, skill_id):
    skill = get_object_or_404(Skill, id=skill_id)

    if request.user == skill.owner:
        messages.warning(request, "You can't request an exchange on your own skill.")
        return redirect('home')

    exchange = ExchangeRequest.objects.create(
        sender=request.user,
        receiver=skill.owner,
        skill=skill,
        message="I would like to exchange skills"
    )

    send_mail(
        subject='New SkillSwap exchange request',
        message=f"{request.user.username} requested an exchange for your skill '{skill.title}'.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[skill.owner.email],
        fail_silently=True,
    )

    messages.success(request, 'Exchange request sent! The other member has been notified.')
    return redirect('home')


def _attach_review_metadata(request_user, exchange_requests):
    for req in exchange_requests:
        req.can_review = False
        req.review_target_id = None

    if request_user.is_staff:
        return

    completed_counts = {}
    for req in exchange_requests:
        if req.status == 'completed' and (req.sender_id == request_user.id or req.receiver_id == request_user.id):
            other_id = req.receiver_id if req.sender_id == request_user.id else req.sender_id
            completed_counts[other_id] = completed_counts.get(other_id, 0) + 1

    if not completed_counts:
        return

    reviewed_counts = dict(
        Review.objects.filter(
            reviewer=request_user,
            reviewed_user_id__in=completed_counts.keys(),
        )
        .values('reviewed_user_id')
        .annotate(total=models.Count('id'))
        .values_list('reviewed_user_id', 'total')
    )

    remaining_reviews = {
        other_id: max(completed_counts[other_id] - reviewed_counts.get(other_id, 0), 0)
        for other_id in completed_counts
    }

    for req in exchange_requests:
        if req.status != 'completed':
            continue
        if req.sender_id != request_user.id and req.receiver_id != request_user.id:
            continue

        other_id = req.receiver_id if req.sender_id == request_user.id else req.sender_id
        req.review_target_id = other_id
        if remaining_reviews.get(other_id, 0) > 0:
            req.can_review = True
            remaining_reviews[other_id] -= 1


@login_required
def manage_requests(request):
    if request.user.is_staff:
        requests = ExchangeRequest.objects.select_related('sender', 'receiver', 'skill').order_by('-created')
    else:
        requests = ExchangeRequest.objects.select_related('sender', 'receiver', 'skill').filter(
            models.Q(receiver=request.user) | models.Q(sender=request.user)
        ).order_by('-created')

    requests = list(requests)
    _attach_review_metadata(request.user, requests)
    return render(request, 'requests.html', {'requests': requests})


@login_required
def accept_request(request, id):
    if request.user.is_staff:
        r = get_object_or_404(ExchangeRequest, id=id)
    else:
        r = get_object_or_404(ExchangeRequest, id=id, receiver=request.user)
    r.status = 'accepted'
    r.save()

    send_mail(
        subject='Your SkillSwap request has been accepted',
        message=f"Your request to exchange for '{r.skill.title}' was accepted.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[r.sender.email],
        fail_silently=True,
    )

    messages.success(request, 'Request accepted. Once the exchange is completed, mark it as finished so a review can be left.')
    return redirect('requests')


@login_required
def refuse_request(request, id):
    if request.user.is_staff:
        r = get_object_or_404(ExchangeRequest, id=id)
    else:
        r = get_object_or_404(ExchangeRequest, id=id, receiver=request.user)
    r.status = 'refused'
    r.save()

    send_mail(
        subject='Your SkillSwap request was refused',
        message=f"Your request to exchange for '{r.skill.title}' was refused.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[r.sender.email],
        fail_silently=True,
    )

    messages.info(request, 'Request refused.')
    return redirect('requests')


@login_required
def complete_exchange(request, id):
    r = get_object_or_404(ExchangeRequest, id=id)
    if not (request.user.is_staff or request.user in {r.sender, r.receiver}):
        messages.error(request, 'You are not allowed to complete this exchange.')
        return redirect('history')

    if r.status != 'accepted':
        messages.warning(request, 'Only accepted exchanges can be marked as completed.')
        return redirect('history')

    r.status = 'completed'
    r.completed_at = timezone.now()
    r.save()

    messages.success(request, 'Exchange marked as completed. You can now leave a review from Requests or History.')
    return redirect('requests')


@login_required
def history(request):
    if request.user.is_staff:
        requests = ExchangeRequest.objects.all().order_by('-created')
    else:
        requests = ExchangeRequest.objects.filter(models.Q(sender=request.user) | models.Q(receiver=request.user)).order_by('-created')

    requests = list(requests)
    _attach_review_metadata(request.user, requests)

    return render(request, 'history.html', {
        'requests': requests,
    })


@login_required
def report_skill(request, skill_id):
    skill = get_object_or_404(Skill, id=skill_id)
    if request.method == 'POST':
        message = request.POST.get('message', '').strip()
        Report.objects.create(reporter=request.user, skill=skill, message=message)
        messages.success(request, 'Your report has been submitted and will be reviewed by an administrator.')
        return redirect('home')

    return render(request, 'report_skill.html', {'skill': skill})


def staff_check(user):
    return (
        user.is_authenticated
        and (user.is_staff or user.is_superuser)
    )


@user_passes_test(staff_check)
def admin_dashboard(request):
    total_users = User.objects.count()
    total_skills = Skill.objects.count()
    total_requests = ExchangeRequest.objects.count()
    pending_reports_count = Report.objects.filter(status='pending').count()
    recent_skills = Skill.objects.order_by('-created')[:10]
    recent_requests = ExchangeRequest.objects.order_by('-created')[:10]
    pending_reports = Report.objects.filter(status='pending').order_by('-created')[:10]

    return render(request, 'admin_dashboard.html', {
        'total_users': total_users,
        'total_skills': total_skills,
        'total_requests': total_requests,
        'pending_reports_count': pending_reports_count,
        'recent_skills': recent_skills,
        'recent_requests': recent_requests,
        'pending_reports': pending_reports,
    })


@user_passes_test(staff_check)
def admin_users(request):
    users = User.objects.order_by('username')
    user_rows = []
    for account in users:
        is_manager = account.is_staff or account.is_superuser
        user_rows.append({
            'account': account,
            'is_manager': is_manager,
        })
    return render(request, 'admin_users.html', {'user_rows': user_rows})


@user_passes_test(staff_check)
def admin_toggle_active(request, id):
    if request.method != 'POST':
        return redirect('admin_users')

    account = get_object_or_404(User, id=id)
    if account.id == request.user.id:
        messages.warning(request, 'You cannot disable your own account from this page.')
        return redirect('admin_users')
    if account.is_superuser:
        messages.warning(request, 'Superuser activation state cannot be changed here.')
        return redirect('admin_users')

    account.is_active = not account.is_active
    account.save(update_fields=['is_active'])
    if account.is_active:
        messages.success(request, f'{account.username} account has been re-activated.')
    else:
        messages.info(request, f'{account.username} account has been disabled.')
    return redirect('admin_users')


@user_passes_test(staff_check)
def admin_skills(request):
    skills = Skill.objects.order_by('-created')
    return render(request, 'admin_skills.html', {'skills': skills})


@user_passes_test(staff_check)
def admin_edit_skill(request, id):
    skill = get_object_or_404(Skill, id=id)
    form = SkillForm(request.POST or None, instance=skill)
    if form.is_valid():
        form.save()
        messages.success(request, 'Skill updated successfully.')
        return redirect('admin_skills')
    return render(request, 'admin_edit_skill.html', {'form': form, 'skill': skill})


@user_passes_test(staff_check)
def admin_delete_skill(request, id):
    skill = get_object_or_404(Skill, id=id)
    if request.method == 'POST':
        skill.delete()
        messages.success(request, 'Skill deleted.')
        return redirect('admin_skills')
    return render(request, 'admin_delete_skill.html', {'skill': skill})


@user_passes_test(staff_check)
def admin_requests(request):
    requests = ExchangeRequest.objects.order_by('-created')
    return render(request, 'admin_requests.html', {'requests': requests})


@user_passes_test(staff_check)
def admin_delete_request(request, id):
    req = get_object_or_404(ExchangeRequest, id=id)
    if request.method == 'POST':
        req.delete()
        messages.success(request, 'Request deleted.')
        return redirect('admin_requests')
    return render(request, 'admin_delete_request.html', {'request_obj': req})


@user_passes_test(staff_check)
def reports_moderation(request):
    reports = Report.objects.all().order_by('-created')
    return render(request, 'moderation_reports.html', {'reports': reports})


@user_passes_test(staff_check)
def resolve_report(request, id, action):
    report = get_object_or_404(Report, id=id)
    if action == 'reviewed':
        report.status = 'reviewed'
        messages.success(request, 'Report marked as reviewed.')
    elif action == 'dismissed':
        report.status = 'dismissed'
        messages.info(request, 'Report dismissed.')
    report.save()
    return redirect('moderation_reports')
