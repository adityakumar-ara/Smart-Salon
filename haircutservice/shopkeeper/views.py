from django.shortcuts import render, redirect
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
            role =request.POST.get('role')

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