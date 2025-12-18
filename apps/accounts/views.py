"""
ARDT FMS - Account Views
Version: 5.4 - Sprint 1

Authentication and user profile views.
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    PasswordChangeDoneView,
    PasswordChangeView,
    PasswordResetCompleteView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetView,
)
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import UpdateView

from .forms import CustomAuthenticationForm, UserPreferenceForm, UserProfileForm
from .models import User, UserPreference


class CustomLoginView(LoginView):
    """
    Custom login view with ARDT branding and remember me functionality.
    """

    template_name = "accounts/login.html"
    form_class = CustomAuthenticationForm
    redirect_authenticated_user = True

    def get_success_url(self):
        """Redirect to dashboard after successful login"""
        return reverse_lazy("dashboard:home")

    def form_valid(self, form):
        """Handle successful login"""
        remember_me = form.cleaned_data.get("remember_me")

        if not remember_me:
            # Session expires when browser closes
            self.request.session.set_expiry(0)
            self.request.session.modified = True
        else:
            # Session expires after 2 weeks
            self.request.session.set_expiry(1209600)  # 14 days in seconds

        # Show welcome message
        user = form.get_user()
        messages.success(self.request, f"Welcome back, {user.get_full_name() or user.username}!")

        return super().form_valid(form)

    def form_invalid(self, form):
        """Handle failed login"""
        messages.error(self.request, "Invalid username or password. Please try again.")
        return super().form_invalid(form)


class CustomLogoutView(LogoutView):
    """Custom logout view with message"""

    next_page = "accounts:login"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.info(request, "You have been logged out successfully.")
        return super().dispatch(request, *args, **kwargs)


@login_required
def profile_view(request):
    """
    User profile page showing user information and recent activity.
    """
    user = request.user

    # Get user's roles
    roles = user.roles.all().order_by("-level")

    # Get user's recent work orders (if technician)
    recent_work_orders = user.assigned_work_orders.all().order_by("-created_at")[:5]

    context = {
        "profile_user": user,
        "roles": roles,
        "department": user.department,
        "position": user.position,
        "recent_work_orders": recent_work_orders,
    }

    return render(request, "accounts/profile.html", context)


@login_required
def settings_view(request):
    """
    User settings page for profile and preferences.
    """
    user = request.user

    # Get or create user preferences
    preferences, created = UserPreference.objects.get_or_create(user=user)

    if request.method == "POST":
        form_type = request.POST.get("form_type", "profile")

        if form_type == "profile":
            profile_form = UserProfileForm(request.POST, instance=user)
            preferences_form = UserPreferenceForm(instance=preferences)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, "Profile updated successfully!")
                return redirect("accounts:settings")
        elif form_type == "preferences":
            profile_form = UserProfileForm(instance=user)
            preferences_form = UserPreferenceForm(request.POST, instance=preferences)
            if preferences_form.is_valid():
                preferences_form.save()
                messages.success(request, "Preferences updated successfully!")
                return redirect("accounts:settings")
        else:
            profile_form = UserProfileForm(instance=user)
            preferences_form = UserPreferenceForm(instance=preferences)
    else:
        profile_form = UserProfileForm(instance=user)
        preferences_form = UserPreferenceForm(instance=preferences)

    context = {
        "profile_form": profile_form,
        "preferences_form": preferences_form,
        "themes": [
            {"value": "light", "label": "Light"},
            {"value": "dark", "label": "Dark"},
            {"value": "auto", "label": "Auto (System)"},
        ],
        "languages": [
            {"value": "en", "label": "English"},
            {"value": "ar", "label": "Arabic (عربي)"},
        ],
    }

    return render(request, "accounts/settings.html", context)


# Password Change Views
class CustomPasswordChangeView(PasswordChangeView):
    """Custom password change view"""

    template_name = "accounts/password_change.html"
    success_url = reverse_lazy("accounts:password_change_done")

    def form_valid(self, form):
        messages.success(self.request, "Your password has been changed successfully!")
        return super().form_valid(form)


class CustomPasswordChangeDoneView(PasswordChangeDoneView):
    """Password change success page"""

    template_name = "accounts/password_change_done.html"


# Password Reset Views
class CustomPasswordResetView(PasswordResetView):
    """Custom password reset initiation view"""

    template_name = "accounts/password_reset.html"
    email_template_name = "accounts/password_reset_email.html"
    subject_template_name = "accounts/password_reset_subject.txt"
    success_url = reverse_lazy("accounts:password_reset_done")


class CustomPasswordResetDoneView(PasswordResetDoneView):
    """Password reset email sent confirmation"""

    template_name = "accounts/password_reset_done.html"


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    """Password reset form"""

    template_name = "accounts/password_reset_confirm.html"
    success_url = reverse_lazy("accounts:password_reset_complete")


class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    """Password reset success page"""

    template_name = "accounts/password_reset_complete.html"
