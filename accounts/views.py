from django.shortcuts import render, redirect
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, logout
from accounts.models import Subscription, Notification
from music.models import Artist
from .forms import RegisterForm
from .forms import ProfileForm
from django.contrib.auth.decorators import login_required
from .models import Profile


@login_required
def edit_profile(request):
    profile = request.user.profile

    if request.method == 'POST':

        form = ProfileForm(request.POST, request.FILES, instance=profile)

        if form.is_valid():
            form.save()

            return redirect('profile')

    else:

        form = ProfileForm(
            instance=profile
        )

    return render(request, 'accounts/edit_profile.html', {'form': form})


def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)

        if form.is_valid():
            form.save()

            return redirect('login')

    else:
        form = RegisterForm()

    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)

        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')

    else:
        form = AuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('home')

def profile_view(request):
    subscription = None
    profile, created = Profile.objects.get_or_create(user=request.user)
    # ۱. ابتدا نوتیفیکیشن‌های خوانده نشده را پیدا می‌کنیم
    notifications = Notification.objects.filter(user=request.user, is_read=False)
    # ۲. تعداد آن‌ها را برای فرستادن به قالب (Template) ذخیره می‌کنیم
    unread_notifications = notifications.count()

    if request.user.is_authenticated:
        try:
            subscription = Subscription.objects.get(user=request.user)
        except Subscription.DoesNotExist:
            pass

    # ۳. حالا وضعیت آن‌ها را به «خوانده شده» تغییر می‌دهیم
    # (این کار بعد از گرفتن تعداد انجام می‌شود تا تعداد صفر نشان داده نشود،
    # اما در دفعات بعدی تعداد صفر خواهد بود)
    notifications.update(is_read=True)

    return render(
        request,
        'accounts/profile.html',
        {'subscription': subscription, "profile": profile, "unread_notifications": unread_notifications}
    )


@login_required
def followed_artists(request):
    artists = Artist.objects.filter(
        artistfollow__user=request.user
    )

    return render(
        request,
        'accounts/followed_artists.html',
        {
            'artists': artists
        }
    )


@login_required
def notifications(request):
    notifications = Notification.objects.filter(user=request.user)

    return render(request, 'accounts/notifications.html', {'notifications': notifications})


@login_required
def profile_settings(request):
    profile = request.user.profile

    if request.method == 'POST':
        request.user.username = request.POST.get('username')
        request.user.email = request.POST.get('email')
        profile.bio = request.POST.get('bio')

        if 'avatar' in request.FILES:
            profile.avatar = request.FILES['avatar']

        request.user.save()
        profile.save()

        return redirect('profile')

    return render(request, 'accounts/profile_settings.html', {'profile': profile})


@login_required
def delete_account(request):
    if request.method == 'POST':
        user = request.user
        logout(request)
        user.delete()
        return redirect('home')

    return render(request,'accounts/delete_account.html')
