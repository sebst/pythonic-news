from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.contrib.auth import logout as do_logout
from django.urls import reverse
from django.conf import settings
from django.utils import timezone


from .models import CustomUser, Invitation, EmailVerification
from .forms import ProfileForm, RegisterForm, CreateInviteForm, PasswordForgottenForm, PasswortResetForm


def profile(request, username=None):
    if username is None:
        return my_profile(request)
    profile = get_object_or_404(CustomUser, username=username)
    if profile == request.user:
        return my_profile(request)
    return render(request, 'accounts/profile.html', {'profile': profile})


@login_required
def my_profile(request):
    instance = request.user
    form = ProfileForm(request.POST or None, instance=instance)
    if request.user.email:
        verifications = EmailVerification.objects.filter(user=request.user, email=request.user.email)
        verified = any([i.verified for i in verifications])
    else:
        verified = False
    if request.method == 'POST':
        if form.is_valid():
            instance = form.save()
            return HttpResponseRedirect(instance.get_absolute_url())
    return render(request, 'accounts/my_profile.html', {'form': form, 'verified': verified})


@login_required
def create_invite(request):
    instance = Invitation(inviting_user = request.user)
    form = CreateInviteForm(request.POST or None, instance=instance)
    if request.method=="POST":
        if form.is_valid():
            instance = form.save()
            return HttpResponseRedirect(instance.get_absolute_url())
    return render(request, 'accounts/create_invite.html', {'form': form})


@login_required
def invite(request, pk):
    invitation = get_object_or_404(Invitation, pk=pk)
    return render(request, 'accounts/invite.html', {'invitation': invitation})


def register(request):
    invite_code = request.GET.get('invite')
    try:
        invitation = Invitation.objects.get(invite_code=invite_code)
    except:
        invitation = None
    instance = CustomUser(used_invitation=invitation, 
                          parent=getattr(invitation, 'inviting_user', None), 
                          email=getattr(invitation, 'invited_email_address', None))
    if not settings.ACCEPT_UNINVITED_REGISTRATIONS and (invitation is None or not getattr(invitation, 'active', False)):
        return render(request, 'accounts/register_closed.html')
    form = RegisterForm(request.POST or None, instance=instance)
    if request.method == 'POST':
        if form.is_valid():
            instance = form.save()
            instance.set_password(form.cleaned_data['password'])
            instance.is_active = True
            instance.save()
            login(request, instance)
            return HttpResponseRedirect(instance.get_absolute_url())
    return render(request, 'accounts/register.html', {'form': form})


def verify(request, verification_code):
    verification = get_object_or_404(EmailVerification, verification_code=verification_code)
    assert verification.user.email == verification.email
    verification.verified = True
    verification.verified_at = timezone.now()
    verification.save()
    return render(request, 'accounts/verify.html')

@login_required
def resend_verification(request):
    if request.method=="POST":
        assert request.user.email
        verification = EmailVerification(user=request.user, email=request.user.email)
        verification.save()
        return render(request, 'accounts/resend_verification.html')


def user_tree(request):
    users = CustomUser.objects.all()
    return render(request, 'accounts/user_tree.html', {'users': users})


def password_forgotten(request, verification_code=None):
    assert not request.user.is_authenticated
    error = None
    if verification_code is None:
        if 'sent' in request.GET.keys():
            return render(request, 'accounts/password_forgotten_sent.html', {})
        form = PasswordForgottenForm(request.POST or None)
        if form.is_valid():
            user = None
            try:
                username = form.cleaned_data['username']
                user = CustomUser.objects.get_by_natural_key(username)
            except:
                pass
            if user:
                if user.email == user.latest_verified_email:
                    reset_request = PasswordResetRequest(user=user)
                    reset_request.save()
                    return HttpResponseRedirect(reverse('password_forgotten')+'?sent')
                else:
                    error = 'This user does not have a verified email. Please contact support.'
            else:
                error = 'User not found.'
        return render(request, 'accounts/password_forgotten_form.html', {'form': form, 'error': error})
    else:
        reset_request = get_object_or_404(PasswordResetRequest, verification_code=verification_code)
        form = PasswortResetForm(request.POST or None)
        if request.method=="POST":
            if form.is_valid():
                reset_request.user.set_password(form.cleaned_data['password']) # TODO: confirm password, password rules
                reset_request.user.save()
                return HttpResponseRedirect(reverse('/login'))
        return render(request, 'accounts/password_forgotten_form.html', {'form': form})


@login_required
def logout(request):
    if request.method=="POST":
        do_logout(request)
        redirect_url = settings.LOGOUT_REDIRECT_URL or '/'
        return HttpResponseRedirect(redirect_url)
    else:
        return render(request, 'accounts/logout.html')

