from django.shortcuts import render, redirect, get_object_or_404
from accounts .models import CustomUser
from .models import Salon, SalonImage 
from django.contrib import messages
from django.contrib.auth.decorators import login_required

@login_required(login_url='login')
def opensalon(request):

    if request.method == "POST":

        gender = request.POST.get('gender')

        Salon.objects.create(
            owner=request.user,
            owner_name=request.POST.get('owner_name'),
            salon_name=request.POST.get('salon_name'),
            address=request.POST.get('address'),
            open_time=request.POST.get('open_time'),
            close_time=request.POST.get('close_time'),
            description=request.POST.get('description'),
        )
        
        image = request.FILES.get('image')

        if image:
            SalonImage.objects.create(
                salon=Salon,
                image=image
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
def salon_detail(request):
    my_salon = Salon.objects.filter( owner=request.user).first()
    context = {
        'salon' : my_salon
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
        messages.success(request, "Salon ki details successfully update ho gayi hain! 🎉")
        return redirect('salon_detail')  
    context = {
        'updatesalon':editsalon,
        'updateCustonUse' : editCustomUser,
    } 
    
    return render(request,'shopkeeper/updatesalon.html', context)    