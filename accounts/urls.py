from django.urls import path
from django.contrib.auth import views as auth_views
from .views import (register_view, login_view, logout_view, profile_view, edit_profile, followed_artists, notifications,
                    profile_settings, delete_account)

urlpatterns = [

    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('profile/', profile_view, name='profile'),
    path('edit-profile/', edit_profile, name='edit_profile'),
    path('followed-artists/', followed_artists, name='followed_artists'),
    path('notifications/', notifications, name='notifications'),
    path('password-reset/', auth_views.PasswordResetView.as_view(template_name='accounts/password_reset.html'),
         name='password_reset'),
    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(template_name='accounts/password_reset_done.html'),
         name='password_reset_done'),
    path('reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(template_name='accounts/password_reset_confirm.html'),
         name='password_reset_confirm'),
    path('reset/done/',
         auth_views.PasswordResetCompleteView.as_view(template_name='accounts/password_reset_complete.html'),
         name='password_reset_complete'), path('settings/', profile_settings, name='profile_settings'),
    path('change-password/', auth_views.PasswordChangeView.as_view(template_name='accounts/change_password.html'),
         name='change_password'),
    path('change-password/done/',
         auth_views.PasswordChangeDoneView.as_view(template_name='accounts/change_password_done.html'),
         name='password_change_done'),
    path('delete-account/', delete_account, name='delete_account'),
]
