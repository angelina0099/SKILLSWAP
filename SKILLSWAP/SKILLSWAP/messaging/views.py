from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .models import Message


@login_required
def inbox(request):
    user_messages = Message.objects.filter(
        Q(sender=request.user) | Q(receiver=request.user)
    ).select_related('sender', 'receiver').order_by('-created')

    conversations_by_user = {}
    for msg in user_messages:
        other_user = msg.receiver if msg.sender_id == request.user.id else msg.sender
        if other_user.id not in conversations_by_user:
            conversations_by_user[other_user.id] = {
                'user': other_user,
                'last_message': msg,
                'last_from_me': msg.sender_id == request.user.id,
            }

    conversations = list(conversations_by_user.values())
    return render(request, 'inbox.html', {'conversations': conversations})


@login_required
def send_message(request, user_id):
    user = get_object_or_404(User, id=user_id)

    if user.id == request.user.id:
        messages.info(request, 'You are already viewing your own account.')
        return redirect('profile', user_id=request.user.id)

    if request.method == 'POST':
        text = request.POST.get('text', '').strip()
        if not text:
            messages.warning(request, 'Please type a message before sending.')
        else:
            Message.objects.create(
                sender=request.user,
                receiver=user,
                text=text,
            )
            return redirect('send_message', user_id=user.id)

    conversation = Message.objects.filter(
        (Q(sender=request.user, receiver=user) | Q(sender=user, receiver=request.user))
    ).select_related('sender', 'receiver').order_by('created')

    return render(request, 'chat.html', {
        'user': user,
        'conversation': conversation,
    })
