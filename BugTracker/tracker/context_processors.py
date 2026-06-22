from .models import Notification

def global_settings(request):
    if request.user.is_authenticated:
        unread_notifications = Notification.objects.filter(recipient=request.user, is_read=False)
        unread_count = unread_notifications.count()
        
        # Get role safely
        role = None
        if hasattr(request.user, 'profile'):
            role = request.user.profile.role
            
        return {
            'global_unread_notifications': unread_notifications[:5],
            'global_unread_count': unread_count,
            'global_user_role': role,
        }
    return {
        'global_unread_notifications': [],
        'global_unread_count': 0,
        'global_user_role': None,
    }
