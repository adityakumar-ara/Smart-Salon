from django.shortcuts import render, redirect, get_object_or_404
from accounts .models import CustomUser
from .models import *
from django.contrib import messages
from django.contrib.auth.decorators import login_required

@login_required(login_url='login')
def opensalon(request):

    if request.method == "POST":

        gender = request.POST.get('gender')
        image_file = request.FILES.get('salon_image')
        new_salon= Salon.objects.create(
            owner=request.user,
            owner_name=request.POST.get('owner_name'),
            salon_name=request.POST.get('salon_name'),
            salon_image=image_file,
            address=request.POST.get('address'),
            open_time=request.POST.get('open_time'),
            close_time=request.POST.get('close_time'),
            description=request.POST.get('description'),
        )
        
        image = request.FILES.get('image')

        if image:
            SalonImage.objects.create(
                salon=new_salon,
                image=image,
                gender = gender,
            )

        messages.success(request, "Salon created successfully 🎉")
        return redirect('home')

    salons = Salon.objects.all()

    return render(request, 'shopkeeper/opensalon.html', {
        'salons': salons
    })


def home(request):
    
    all_salons = Salon.objects.all()

    
    context = {'salons': all_salons}
    return render(request, 'home.html', context)


@login_required(login_url='login')
def salon_views(request):

    my_salon = Salon.objects.filter(owner=request.user).first()
    if my_salon:
        salon_gallery = SalonImage.objects.filter(salon=my_salon)
    else:
        salon_gallery = SalonImage.objects.none()    
    context = {
        'salon' : my_salon,
        'saved_gallery':salon_gallery,
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

        editsalon.address = request.POST.get('address',editsalon.address)
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
                if g_image or g_desc:
                    SalonImage.objects.create(
                        salon=editsalon, # ⚠️ Agar aapke model mein ForeignKey ka naam 'salon' ki jagah kuch aur hai toh wo likhein
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
       service_name = request.POST.get('service_name')
       service_price = request.POST.get('service_price')
       about_service = request.POST.get('about_service')
       service_image = request.FILES.get('service_image')
       
       try:
            # Apne models.py ke hisaab se check kar lein (owner=request.user ya user=request.user)
            current_salon = Salon.objects.filter(owner=request.user).first() 
       except Salon.DoesNotExist:
            messages.error(request, "Pehle aapko apna Salon register karna padega!")
            return redirect('home') 

       new_service = Service.objects.create(
        salon=current_salon,
        service_name = service_name,
        service_price =service_price,
        about_service = about_service,
        service_image = service_image,
        )
       messages.success(request,"Your Service is added ")
       return redirect('add_service')
    return render(request,'shopkeeper/salon_service.html')
