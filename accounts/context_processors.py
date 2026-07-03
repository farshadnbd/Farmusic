from accounts.models import Notification


def notifications_count(request):

    count = 0

    if request.user.is_authenticated:

        count = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).count()

    return {
        'unread_notifications': count
    }