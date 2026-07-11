from django.shortcuts import render, redirect, get_object_or_404
from accounts.models import CustomUser
from .models import Salon, SalonImage, SalonService, QueueEntry, SiderImage
from django.contrib import messages
from django.contrib.auth.decorators import login_required

@login_required(login_url='login')
def opensalon(request):

    existing_by_owner = Salon.objects.filter(owner=request.user).exists()
    existing_by_email = Salon.objects.filter(owner__email=request.user.email).exclude(owner=request.user).exists()
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

    salons = Salon.objects.all()

    return render(request, 'shopkeeper/opensalon.html', {
        'salons': salons
    })


def home(request):
    all_salons = Salon.objects.all()
    # Improvement: Only fetch slider images that actually have an image file.
    slider_images = SiderImage.objects.exclude(image__isnull=True).exclude(image__exact='')
    user_queue_ids = []
    if request.user.is_authenticated and hasattr(request.user, 'is_customer') and request.user.is_customer:
        user_queue_ids = list(QueueEntry.objects.filter(customer=request.user, status='waiting').values_list('salon_id', flat=True))

    context = {
        'salons': all_salons,
        'user_queue_ids': user_queue_ids,
        "slide_image" : slider_images,
    }
    return render(request, 'home.html', context)


def salon_detail_public(request, salon_id):
    salon = get_object_or_404(Salon, id=salon_id)
    services = SalonService.objects.filter(salon=salon)
    gallery_images = SalonImage.objects.filter(salon=salon)
    
    user_queue_ids = []
    current_booking = None
    if request.user.is_authenticated and hasattr(request.user, 'is_customer') and request.user.is_customer:
        user_queue_ids = list(QueueEntry.objects.filter(customer=request.user, status='waiting').values_list('salon_id', flat=True))
        current_booking = QueueEntry.objects.filter(customer=request.user, status__in=['waiting', 'seated']).select_related('service').first()

    context = {
        'salon': salon,
        'services': services,
        'gallery_images': gallery_images,
        'user_queue_ids': user_queue_ids,
        'current_booking': current_booking,
    }
    return render(request, 'shopkeeper/salon_detail_public.html', context)

@login_required(login_url='login')
def join_queue(request, service_id):
    service = get_object_or_404(SalonService, id=service_id)
    salon = service.salon
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
    messages.success(request, f'Booked sit for {service.name} at {salon.salon_name}. Your waiting position is {entry.position}.')
    return redirect(request.META.get('HTTP_REFERER') or 'home')


@login_required(login_url='login')
def leave_queue(request, service_id):
    service = get_object_or_404(SalonService, id=service_id)
    entry = QueueEntry.objects.filter(service=service, customer=request.user, status='waiting').first()
    if not entry:
        messages.error(request, 'You do not have an active waiting booking for this service.')
        return redirect(request.META.get('HTTP_REFERER') or 'home')

    entry.status = 'cancelled'
    entry.save()
    messages.success(request, f'Your booking for {service.name} has been cancelled.')
    return redirect(request.META.get('HTTP_REFERER') or 'home')


@login_required(login_url='login')
def accept_order(request, entry_id):
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
    entry = get_object_or_404(QueueEntry, id=entry_id, salon__owner=request.user)
    if entry.status not in ['waiting', 'seated']:
        messages.info(request, 'This order cannot be cancelled.')
        return redirect('salon_detail')
    entry.status = 'cancelled'
    entry.save()
    messages.success(request, f'Booking for {entry.customer.username} has been cancelled.')
    return redirect('salon_detail')


@login_required(login_url='login')
def salon_views(request):

    my_salon = Salon.objects.filter(owner=request.user).first()
    if my_salon:
        salon_gallery = SalonImage.objects.filter(salon=my_salon)
        queue_entries = my_salon.queue_entries.filter(status__in=['waiting', 'seated']).select_related('customer', 'service')
    else:
        salon_gallery = SalonImage.objects.none()
        queue_entries = QueueEntry.objects.none()
    context = {
        'salon': my_salon,
        'saved_gallery': salon_gallery,
        'queue_entries': queue_entries,
    }
    return render(request, 'shopkeeper/salonviews.html', context)

@login_required(login_url='login')
def edit_salon(request):
    editsalon = Salon.objects.filter(owner=request.user).first()
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
        return redirect('salon_views')

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
       
       current_salon = Salon.objects.filter(owner=request.user).first()
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

    current_salon = Salon.objects.filter(owner=request.user).first()
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
    service = get_object_or_404(SalonService, id=service_id, salon__owner=request.user)
    
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
    
    service = get_object_or_404(SalonService, id=service_id, salon__owner=request.user)
    
    service.delete()
    messages.success(request, "Service deleted successfully! 🗑️")
    return redirect('service_views')

def male_section(request):
    
    male_service = SalonService.objects.filter(target_gender__in=['male', 'unisex'])
    current_booking = None
    if request.user.is_authenticated and hasattr(request.user, 'is_customer') and request.user.is_customer:
        current_booking = QueueEntry.objects.filter(customer=request.user, status='waiting').select_related('service').first()
    context = {
        'services': male_service,
        'current_booking': current_booking,
    }
    return render(request, 'shopkeeper/maleservice.html', context)
def female_section(request):
    
    female_service = SalonService.objects.filter(target_gender__in=['female', 'unisex'])
    current_booking = None
    if request.user.is_authenticated and hasattr(request.user, 'is_customer') and request.user.is_customer:
        current_booking = QueueEntry.objects.filter(customer=request.user, status='waiting').select_related('service').first()
    context = {
        'services': female_service,
        'current_booking': current_booking,
    }
    return render(request, 'shopkeeper/femaleservice.html', context)

def about_service_page(request,service_id):
    service_data = get_object_or_404(SalonService, id=service_id, is_active = True)
    current_booking = None
    if request.user.is_authenticated and hasattr(request.user, 'is_customer') and request.user.is_customer:
        current_booking = QueueEntry.objects.filter(customer=request.user, status__in=['waiting', 'seated']).select_related('service').first()

    context = {
        'service':service_data,
        'current_booking': current_booking,
    }
    return render(request,'shopkeeper/about_seervice_page.html', context)