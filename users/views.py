from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from core.models import ReadingProgress, UserLibrary

@login_required
def profile(request):
    user = request.user
    user_profile = getattr(user, "profile", None)
    
    last_read = ReadingProgress.objects.select_related("book", "page")\
        .filter(user=user).order_by("-updated_at").first()
    
    library_stats = {
        'reading': UserLibrary.objects.filter(user=user, status='reading').count(),
        'finished': UserLibrary.objects.filter(user=user, status='finished').count(),
        'wishlist': UserLibrary.objects.filter(user=user, status='wishlist').count(),
    }

    return render(
        request,
        "users/profile.html",
        {
            "user": user,
            "profile": user_profile,
            "last_read": last_read,
            "stats": library_stats,
        },
    )