from shopkeeper.models import Salon


def has_salon_context_processor(request):
    has_salon = False
    if request.user.is_authenticated:
        has_salon = Salon.objects.filter(owner=request.user, is_active=True).exists()
    return {'has_salon': has_salon}
