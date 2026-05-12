def language(request):
    current_language = request.session.get("site_language", "fr")
    return {
        "current_language": current_language,
        "is_ar": current_language == "ar",
    }


def unread_notifications(request):
    """Expose unread notification count to the navbar."""
    if request.user.is_authenticated:
        return {"unread_notifications_count": request.user.notifications.filter(is_read=False).count()}
    return {"unread_notifications_count": 0}
