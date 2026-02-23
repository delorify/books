from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def profile(request):
    """
    Simple profile page for the current user.
    This matches Django's default /accounts/profile/ redirect target.
    """
    user = request.user
    profile = getattr(user, "profile", None)
    return render(
        request,
        "users/profile.html",
        {
            "user": user,
            "profile": profile,
        },
    )

