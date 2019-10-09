from django.urls import path, include

from . import views
from django.contrib.auth import views as auth_views



urlpatterns = [
    path('profile', views.profile, name="accounts_my_profile"),
    path('profile/<str:username>', views.profile, name="accounts_profile"),

    path('user-tree', views.user_tree, name="accounts_user_tree"),

    path('create-invite', views.create_invite, name="accounts_create_invite"),
    path('invite/<uuid:pk>', views.invite, name="accounts_invite"),

    path('verify/<uuid:verification_code>', views.verify, name="accounts_verify"),
    path('resend-verification', views.resend_verification, name="accounts_resend_verification"),

    path('register', views.register, name="accounts_register"),
    
    # path('accounts/', include('django.contrib.auth.urls')), # new
    path('accounts/login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name="login"),
    #path('accounts/logout/', auth_views.LogoutView.as_view(template_name='accounts/logout.html'), name="logout"),
    path('accounts/logout/', views.logout, name="logout"),
    path('accounts/password-change/', auth_views.PasswordChangeView.as_view(template_name='accounts/password_change_form.html'), name="password_change"),
    path('accounts/password-change-done/', auth_views.PasswordChangeDoneView.as_view(template_name='accounts/password_change_done.html'), name="password_change_done"),

    path('accounts/password-forgotten/', views.password_forgotten, name="password_forgotten"),
    path('accounts/password-forgotten/<str:verification_code>', views.password_forgotten, name="password_forgotten"),


]
