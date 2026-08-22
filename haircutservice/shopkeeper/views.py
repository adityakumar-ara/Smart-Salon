from math import radians, sin, cos, asin, sqrt
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from accounts.models import CustomUser
from .models import Salon, SalonImage, SalonService, QueueEntry, SiderImage, SalonFeedback
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from webpush import send_user_notification
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
import random
import time


def _haversine_km(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    return 6371 * c


def nearby_salons_api(request):
    lat = request.GET.get('lat')
    lng = request.GET.get('lng')
    radius_km = request.GET.get('radius', 15)

    if lat is None or lng is None:
        return JsonResponse({'error': 'Please provide latitude and longitude.'}, status=400)

    try:
        lat = float(lat)
        lng = float(lng)
        radius_km = float(radius_km)
    except ValueError:
        return JsonResponse({'error': 'Invalid coordinates.'}, status=400)

    salons = Salon.objects.filter(is_active=True).exclude(latitude__isnull=True).exclude(longitude__isnull=True)
    nearby = []
    for salon in salons:
        distance = _haversine_km(lat, lng, salon.latitude, salon.longitude)
        if distance <= radius_km:
            nearby.append({
                'id': salon.id,
                'name': salon.salon_name,
                'distance': round(distance, 1),
                'url': f'/shopkeeper/salon/{salon.id}/',
            })

    nearby.sort(key=lambda item: item['distance'])
    return JsonResponse({'salons': nearby[:20], 'total': len(nearby)})

@login_required(login_url='login')
def opensalon(request):

    existing_by_owner = Salon.objects.filter(owner=request.user, is_active=True).exists()
    existing_by_email = Salon.objects.filter(owner__email=request.user.email, is_active=True).exclude(owner=request.user).exists()
    if existing_by_owner or existing_by_email:
        messages.error(request, "Salon alredy open this Email ")
        return redirect('home')

    if request.method == "POST":

        image_file = request.FILES.get('salon_image')
        latitude = request.POST.get('latitude')
        longitude = request.POST.get('longitude')
        new_salon = Salon.objects.create(
            owner=request.user,
            owner_name=request.POST.get('owner_name'),
            salon_name=request.POST.get('salon_name'),
            salon_image=image_file,
            latitude=float(latitude) if latitude else None,
            longitude=float(longitude) if longitude else None,
            open_time=request.POST.get('open_time'),
            close_time=request.POST.get('close_time'),
            description=request.POST.get('description'),
        )
        
        image = request.FILES.get('image')

        if image:
            SalonImage.objects.create(
                salon=new_salon,
                image=image,
            )

        messages.success(request, "Salon created successfully 🎉")
        return redirect('home')

    salons = Salon.objects.filter(is_active=True)

    return render(request, 'shopkeeper/opensalon.html', {
        'salons': salons
    })


def home(request):
    all_salons = Salon.objects.filter(is_active=True)
    has_salon = False
    if request.user.is_authenticated:
        has_salon = Salon.objects.filter(owner=request.user, is_active=True).exists()

    # Improvement: Only fetch slider images that actually have an image file.
    slider_images = SiderImage.objects.exclude(image__isnull=True).exclude(image__exact='')
    user_queue_ids = []
    if request.user.is_authenticated and hasattr(request.user, 'is_customer') and request.user.is_customer:
        user_queue_ids = list(QueueEntry.objects.filter(customer=request.user, status='waiting').values_list('salon_id', flat=True))

    context = {
        'salons': all_salons,
        'user_queue_ids': user_queue_ids,
        "slide_image" : slider_images,
        "has_salon": has_salon,
    }
    return render(request, 'home.html', context)


def salon_detail_public(request, salon_id):
    salon = get_object_or_404(Salon, id=salon_id, is_active=True)
    services = SalonService.objects.filter(salon=salon)
    gallery_images = SalonImage.objects.filter(salon=salon)
    
    feedbacks = salon.feedbacks.select_related('customer').all()
    feedback_count = feedbacks.count()
    average_rating = round(sum(feedback.rating for feedback in feedbacks) / feedback_count, 1) if feedback_count else None
    user_has_feedback = False

    user_queue_ids = []
    current_booking = None
    if request.user.is_authenticated and hasattr(request.user, 'is_customer') and request.user.is_customer:
        user_queue_ids = list(QueueEntry.objects.filter(customer=request.user, status='waiting').values_list('salon_id', flat=True))
        current_booking = QueueEntry.objects.filter(customer=request.user, status__in=['waiting', 'seated']).select_related('service', 'salon').first()
    if request.user.is_authenticated:
        if hasattr(request.user, 'is_customer') and request.user.is_customer:
            user_queue_ids = list(QueueEntry.objects.filter(customer=request.user, status='waiting').values_list('salon_id', flat=True))
            current_booking = QueueEntry.objects.filter(customer=request.user, status__in=['waiting', 'seated']).select_related('service', 'salon').first()
        user_has_feedback = salon.feedbacks.filter(customer=request.user).exists()

    context = {
        'salon': salon,
        'services': services,
        'gallery_images': gallery_images,
        'feedbacks': feedbacks,
        'feedback_count': feedback_count,
        'average_rating': average_rating,
        'user_has_feedback': user_has_feedback,
        'user_queue_ids': user_queue_ids,
        'current_booking': current_booking,
    }
    return render(request, 'shopkeeper/salon_detail_public.html', context)

@login_required(login_url='login')
def add_feedback(request, salon_id):
    salon = get_object_or_404(Salon, id=salon_id)
    if request.method != 'POST':
        return redirect('salon_detail_public', salon_id=salon.id)

    if not (hasattr(request.user, 'is_customer') and request.user.is_customer):
        messages.error(request, 'Only customers can leave feedback.')
        return redirect('salon_detail_public', salon_id=salon.id)

    if SalonFeedback.objects.filter(salon=salon, customer=request.user).exists():
        messages.error(request, 'You have already submitted feedback for this salon.')
        return redirect('salon_detail_public', salon_id=salon.id)

    try:
        rating = int(request.POST.get('rating', ''))
    except (TypeError, ValueError):
        rating = 0
    comment = request.POST.get('comment', '').strip()

    if rating not in range(1, 6):
        messages.error(request, 'Please choose a rating from 1 to 5 stars.')
        return redirect('salon_detail_public', salon_id=salon.id)

    SalonFeedback.objects.create(salon=salon, customer=request.user, rating=rating, comment=comment)
    messages.success(request, 'Thank you for sharing your feedback!')
    return redirect('salon_detail_public', salon_id=salon.id)
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from webpush import send_user_notification
# आपके मॉडल्स इम्पोर्ट...

@login_required(login_url='login')
def join_queue(request, service_id):
    service = get_object_or_404(SalonService, id=service_id, salon__is_active=True)
    salon = service.salon
    salon_owner = salon.owner
    if not hasattr(request.user, 'is_customer') or not request.user.is_customer:
        messages.error(request, 'Only customers can book sit for a service.')
        return redirect(request.META.get('HTTP_REFERER') or 'home')

    active_booking = QueueEntry.objects.filter(
        customer=request.user,
        status__in=['waiting', 'seated']
    ).exists()

    if active_booking:
        messages.info(request, 'You already have an active booking. Leave it before booking another service.')
        return redirect(request.META.get('HTTP_REFERER') or 'home')
    entry = QueueEntry.objects.create(salon=salon, service=service, customer=request.user)

    payload = {
        "head": "🔥 नया कस्टमर आ गया!",
        "body": f"कतार में एक नया अपॉइंटमेंट जुड़ गया है। Waiting Position: {entry.position}", 
        "icon": "/static/assest/logosnipalert.svg",
        "url": "/shopkeeper/dashboard/"
    }
    
    try:
        send_user_notification(user=salon_owner, payload=payload, ttl=1000)
    except Exception as e:
        print(f"नोटिफिकेशन भेजने में एरर: {e}")
    messages.success(request, f'Booked sit for {service.name} at {salon.salon_name}. Your waiting position is {entry.position}.')
    return redirect(request.META.get('HTTP_REFERER') or 'home')

@login_required(login_url='login')
def leave_queue(request, service_id):
    service = get_object_or_404(SalonService, id=service_id)
    entry = QueueEntry.objects.filter(service=service, customer=request.user, status__in=['waiting', 'seated']).first()
    if not entry:
        messages.error(request, 'You do not have an active booking for this service.')
        return redirect(request.META.get('HTTP_REFERER') or 'home')

    entry.status = 'cancelled'
    entry.save()
    messages.success(request, f'Your booking for {service.name} has been cancelled.')
    return redirect(request.META.get('HTTP_REFERER') or 'home')


@login_required(login_url='login')
def accept_order(request, entry_id):
    if request.method != 'POST':
        return redirect('salon_detail')
    entry = get_object_or_404(QueueEntry, id=entry_id, salon__owner=request.user)
    if entry.status != 'waiting':
        messages.info(request, 'This order cannot be accepted because it is not waiting.')
        return redirect('salon_detail')
    entry.status = 'seated'
    entry.save()
    messages.success(request, f'{entry.customer.username} has been accepted and seated.')
    return redirect('salon_detail')


@login_required(login_url='login')
def cancel_order(request, entry_id):
    if request.method != 'POST':
        return redirect('salon_detail')
    entry = get_object_or_404(QueueEntry, id=entry_id, salon__owner=request.user)
    if entry.status not in ['waiting', 'seated']:
        messages.info(request, 'This order cannot be cancelled.')
        return redirect('salon_detail')
    entry.status = 'cancelled'
    entry.save()
    messages.success(request, f'Booking for {entry.customer.username} has been rejected.')
    return redirect('salon_detail')


@login_required(login_url='login')
def complete_order(request, entry_id):
    if request.method != 'POST':
        return redirect('salon_detail')
    entry = get_object_or_404(QueueEntry, id=entry_id, salon__owner=request.user)
    if entry.status != 'seated':
        messages.info(request, 'Only an accepted booking can be marked complete.')
        return redirect('salon_detail')
    entry.status = 'completed'
    entry.save()
    messages.success(request, f'Service for {entry.customer.username} marked as completed.')
    return redirect('salon_detail')


@login_required(login_url='login')
def my_booking(request):
    if not hasattr(request.user, 'is_customer') or not request.user.is_customer:
        messages.error(request, 'Only customers can view booking status.')
        return redirect('home')
    booking = QueueEntry.objects.filter(customer=request.user, status__in=['waiting', 'seated']).select_related('salon', 'service').first()
    return render(request, 'shopkeeper/my_booking.html', {'booking': booking})


@login_required(login_url='login')
def salon_views(request):

    my_salon = Salon.objects.filter(owner=request.user, is_active=True).first()
    if my_salon:
        salon_gallery = SalonImage.objects.filter(salon=my_salon)
        queue_entries = my_salon.queue_entries.filter(status__in=['waiting', 'seated']).select_related('customer', 'service')
        
        # Logic to identify new bookings
        seen_bookings = request.session.get('seen_bookings', [])
        for entry in queue_entries:
            if entry.status == 'waiting' and entry.id not in seen_bookings:
                entry.is_new = True
        
        request.session['seen_bookings'] = list(queue_entries.filter(status='waiting').values_list('id', flat=True))
        
        feedbacks = my_salon.feedbacks.select_related('customer').all()
        feedback_count = feedbacks.count()
        average_rating = round(sum(feedback.rating for feedback in feedbacks) / feedback_count, 1) if feedback_count else None
    else:
        salon_gallery = SalonImage.objects.none()
        queue_entries = QueueEntry.objects.none()
        feedbacks = SalonFeedback.objects.none()
        feedback_count = 0
        average_rating = None
    context = {
        'salon': my_salon,
        'saved_gallery': salon_gallery,
        'queue_entries': queue_entries,
        'feedbacks': feedbacks,
        'feedback_count': feedback_count,
        'average_rating': average_rating,
        'rating_stars': range(1, 6),
    }
    return render(request, 'shopkeeper/salonviews.html', context)


@login_required(login_url='login')
def remove_salon(request):
    salon = get_object_or_404(Salon, owner=request.user, is_active=True)

    if request.method == 'POST' and request.POST.get('action') == 'send_otp':
        if request.POST.get('confirm_remove') != 'yes':
            messages.error(request, 'Please confirm that you want to remove your salon.')
            return redirect('remove_salon')

        otp = str(random.randint(100000, 999999))
        request.session['salon_removal_otp'] = otp
        request.session['salon_removal_salon_id'] = salon.id
        request.session['salon_removal_otp_created_at'] = time.time()

        try:
            send_mail(
                'SnipAlert salon removal OTP',
                f'Your OTP to remove {salon.salon_name} is: {otp}\n\nThis OTP expires in 10 minutes. If you did not request this, please ignore this email.',
                settings.DEFAULT_FROM_EMAIL,
                [request.user.email],
                fail_silently=False,
            )
        except Exception:
            messages.error(request, 'We could not send the OTP. Please check your email settings and try again.')
            return redirect('remove_salon')

        messages.success(request, 'An OTP has been sent to your registered email address.')
        return render(request, 'shopkeeper/remove_salon.html', {'salon': salon, 'otp_sent': True})

    if request.method == 'POST' and request.POST.get('action') == 'confirm_remove':
        otp = (request.POST.get('otp') or '').strip()
        otp_created_at = request.session.get('salon_removal_otp_created_at', 0)
        valid_otp = (
            request.session.get('salon_removal_salon_id') == salon.id
            and otp == request.session.get('salon_removal_otp')
            and time.time() - otp_created_at <= 600
        )
        if not valid_otp:
            messages.error(request, 'Invalid or expired OTP. Please request a new one.')
            return render(request, 'shopkeeper/remove_salon.html', {'salon': salon, 'otp_sent': True})

        salon.is_active = False
        salon.removed_at = timezone.now()
        salon.save(update_fields=['is_active', 'removed_at'])
        for key in ('salon_removal_otp', 'salon_removal_salon_id', 'salon_removal_otp_created_at'):
            request.session.pop(key, None)
        messages.success(request, 'Your salon has been removed successfully. Its data has been kept safely.')
        return redirect('home')

    return render(request, 'shopkeeper/remove_salon.html', {'salon': salon})

@login_required(login_url='login')
def edit_salon(request):
    editsalon = Salon.objects.filter(owner=request.user, is_active=True).first()
    if not editsalon:
        messages.error(request ,"You don't have any salon Plz Fisrt register salon")
        return redirect('opensalon')

    editCustomUser = editsalon.owner
    if request.method == "POST":
        editsalon.owner_name = request.POST.get('owner_name',editsalon.owner_name)
        editsalon.salon_name = request.POST.get('salon_name',editsalon.salon_name)
        editCustomUser.mobile = request.POST.get('number',editCustomUser.mobile)
        if request.FILES.get('image'):
               editCustomUser.image = request.FILES.get('image')

        latitude = request.POST.get('latitude')
        longitude = request.POST.get('longitude')
        if latitude:
            editsalon.latitude = float(latitude)
        if longitude:
            editsalon.longitude = float(longitude)

        editsalon.open_time = request.POST.get('open_time',editsalon.open_time)
        editsalon.close_time = request.POST.get('close_time',editsalon.close_time)
        editsalon.description = request.POST.get('description',editsalon.description)
        editsalon.save()
        editCustomUser.save() 
        
        existing_pics = editsalon.images.all() # Pehle se saved photos
        
        for i in range(1, 6):
            g_image = request.FILES.get(f'image_{i}')
            g_desc = request.POST.get(f'img_desc_{i}')
            
            # Agar us slot par pehle se photo hai, toh use UPDATE karo
            if len(existing_pics) >= i:
                pic_to_update = existing_pics[i-1]
                if g_image:
                    pic_to_update.image = g_image
                if g_desc is not None:
                    pic_to_update.description = g_desc
                pic_to_update.save()
            else:
                # Agar us slot par pehle se photo nahi hai, toh NAYI CREATE karo
                if g_image:
                    SalonImage.objects.create(
                        salon=editsalon,
                        image=g_image,
                        description=g_desc
                    )

        messages.success(request, "Salon aur Gallery successfully update ho gayi hain! 🎉")
        return redirect('salon_detail')

    # 3. 🔥 DATA LOAD SYSTEM: Database se data nikaal kar HTML ke 5 slots mein bhejanna
    all_saved_images = editsalon.images.all()
    slots_data = []
    for i in range(1, 6):
        try:
            # Agar database mein ith photo majood hai toh utha lo
            saved_data = all_saved_images[i-1]
        except IndexError:
            # Agar nahi hai toh khali chhod do
            saved_data = None
            
        slots_data.append({
            'index': i,
            'info': saved_data
        })
    context = {
        'updatesalon':editsalon,
        'updateCustonUse' : editCustomUser,
        'slots_data':slots_data,
    } 
    
    return render(request,'shopkeeper/updatesalon.html', context)

@login_required(login_url='login')
def add_service(request):
    if request.method == "POST":
       name = request.POST.get('service_name')
       price = request.POST.get('service_price')
       image = request.FILES.get('service_image')
       target_gender = request.POST.get('target_gender')
       
       current_salon = Salon.objects.filter(owner=request.user, is_active=True).first()
       if not current_salon:
            messages.error(request, "Pehle aapko apna Salon register karna padega!")
            return redirect('opensalon')

       SalonService.objects.create(
            salon=current_salon,
            name=name,
            price=price,
            image=image,
            target_gender=target_gender,
        )
       messages.success(request,"Your Service is added")
       
       return redirect('add_service')
    return render(request,'shopkeeper/salon_service.html')

@login_required(login_url='login')
def service_views(request):

    current_salon = Salon.objects.filter(owner=request.user, is_active=True).first()
    if not current_salon:
         messages.error(request, 'No salon found for your account.')
         return redirect('home')
    all_service = SalonService.objects.filter(salon=current_salon)

    context = {
        'services' : all_service
    }
    return render(request, 'shopkeeper/service_views.html', context)
    
@login_required(login_url='login')
def edit_service(request, service_id):
    service = get_object_or_404(SalonService, id=service_id, salon__owner=request.user, salon__is_active=True)
    
    if request.method == "POST":
        service.name = request.POST.get('service_name')
        service.price = request.POST.get('service_price')
        service.target_gender = request.POST.get('target_gender')
        
        if request.FILES.get('service_image'):
            service.image = request.FILES.get('service_image')
            
        service.save() # Database me update ho gaya
        messages.success(request, "Service updated successfully! 🎉")
        return redirect('service_views') 

    return render(request, 'shopkeeper/editservice.html', {'service': service})



@login_required(login_url='login')
def delete_service(request, service_id):
    
    service = get_object_or_404(SalonService, id=service_id, salon__owner=request.user, salon__is_active=True)
    
    service.delete()
    messages.success(request, "Service deleted successfully! 🗑️")
    return redirect('service_views')

def male_section(request):
    
    male_service = SalonService.objects.filter(salon__is_active=True, target_gender__in=['male', 'unisex'])
    current_booking = None
    if request.user.is_authenticated and hasattr(request.user, 'is_customer') and request.user.is_customer:
        current_booking = QueueEntry.objects.filter(customer=request.user, status__in=['waiting', 'seated']).select_related('service', 'salon').first()
    context = {
        'services': male_service,
        'current_booking': current_booking,
    }
    return render(request, 'shopkeeper/maleservice.html', context)
def female_section(request):
    
    female_service = SalonService.objects.filter(salon__is_active=True, target_gender__in=['female', 'unisex'])
    current_booking = None
    if request.user.is_authenticated and hasattr(request.user, 'is_customer') and request.user.is_customer:
        current_booking = QueueEntry.objects.filter(customer=request.user, status__in=['waiting', 'seated']).select_related('service', 'salon').first()
    context = {
        'services': female_service,
        'current_booking': current_booking,
    }
    return render(request, 'shopkeeper/femaleservice.html', context)

def about_service_page(request,service_id):
    service_data = get_object_or_404(SalonService, id=service_id, is_active=True, salon__is_active=True)
    current_booking = None
    if request.user.is_authenticated and hasattr(request.user, 'is_customer') and request.user.is_customer:
        current_booking = QueueEntry.objects.filter(customer=request.user, status__in=['waiting', 'seated']).select_related('service', 'salon').first()

    context = {
        'service':service_data,
        'current_booking': current_booking,
    }
    return render(request,'shopkeeper/about_seervice_page.html', context)

