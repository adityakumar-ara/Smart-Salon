from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from .models import CustomUser
from shopkeeper.models import Salon

User = get_user_model()

def SignUp(request):
    if request.method == 'POST':
       
        username = request.POST.get('username')
        name = request.POST.get('name')
        mobile = request.POST.get('mobile')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        role = request.POST.get('role')
        
        if password != confirm_password:
            messages.error(request, "password and conformpasswprd must be same.!")
            return redirect(request.META.get('HTTP_REFERER', '/'))
        
        # 2. Username check
        if User.objects.filter(username=username).exists():
            
            messages.error(request, "User already Exissts")
            return redirect(request.META.get('HTTP_REFERER', '/'))

        # 3. Customer Creation
        if role == "customer":
            print("⏳ Customer account ban raha hai...")
            User.objects.create_user(
                username=username,
                name=name,
                mobile=mobile,
                password=password,
                is_customer=True,
            )
            
           
            messages.success(request, f"Customer account successfully , {name}! you can login ")

        # 4. Shopkeeper Creation
        elif role == "shopkeeper":
           
            User.objects.create_user(
                username=username,
                name=name,
                mobile=mobile,
                password=password,
                is_shopkeeper=True
            )
          
            
            messages.success(request, f"Shopkeeper account successfully , {name}! you can login. ")
      
            
        return redirect('login') 
        
    return render(request, 'accounts/signup.html')

def login(request):
    if request.method == "POST":
        username= request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            messages.success(request, f"Welcome {user.username}!")
            return redirect('home')
        else:
            messages.error(request, "Invalid Username or Password. Please try again.")
            return redirect('home')

    salons = Salon.objects.all()
    return render(request, 'home.html', {'salons': salons})

@login_required(login_url='login')
def logout_user (request):
    logout(request)
    messages.info(request, "you have  been logged out")
    return redirect('login')

@login_required(login_url='login')
def profile(request):
    context = {
        'current_user': request.user
    }
    return render(request, 'accounts/profile.html', context)

def editprofile(request, id):
    updateprofile = get_object_or_404(CustomUser, id=id)
    
    if request.method == 'POST':
        new_username = request.POST.get('username')
        form_name = request.POST.get('name')
        
       
        if new_username != updateprofile.username:
            if CustomUser.objects.filter(username=new_username).exists():
                messages.error(request, f"Username '{new_username}' pehle se kisi aur ne liya hua hai!")
                context = {'user': updateprofile}
                return render(request, 'accounts/editprofile.html', context)
        
        updateprofile.username = new_username
        
        if form_name:
            updateprofile.name = form_name
            
        updateprofile.mobile = request.POST.get('mobile', updateprofile.mobile)
        updateprofile.email = request.POST.get('email', updateprofile.email)
        if request.FILES.get('image'):
               updateprofile.image = request.FILES.get('image')

        updateprofile.save()
        messages.success(request, "Profile successfully update ho gayi!")
        return redirect('profile')
        
    context = {'user': updateprofile}
    return render(request, 'accounts/editprofile.html', context)