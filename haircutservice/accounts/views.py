from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib.auth.decorators import login_required


# Create your views here.
User = get_user_model()
def SignUp(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        name = request.POST.get('name')
        mobile = request.POST.get('mobile')
        password = request.POST.get('password')
        conform_password = request.POST.get('conform_password')
        role = request.POST.get('role')
      
        if password != conform_password:
            print("Password must be same")
            return redirect('SignUp')
        #filter username
        if User.objects.filter(username=username).exists():
           messages.error(request, "Username alredy exists")
           return redirect ('SignUp')

        #customer
        if role == "costomer":

            User.objects.create_user(
            username=username,
             name = name,
             mobile = mobile,
             password= password,
             is_customer = True,
            )

        # shopkeeper    
        elif role == "shopkeeper":

            User.objects.create_user(
                username=username,
                name=name,
                mobile=mobile,
                password=password,
                is_shopkeeper=True
            )

        return redirect('login')

    return render(request, 'accounts/signup.html')  

def login(request):
    if request.method == "POST":
        username= request.POST.get('username')
        name = request.POST.get('name')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            messages.success(request, f"Welcome {name}!")
            return redirect('home')
        else:
            
            messages.error(request, "Invalid Name and Password")
            return redirect('login')
    return render(request, 'home.html')  

@login_required(login_url='login')
def profile(request):
    context = {
        'current_user': request.user
    }
    return render(request, 'accounts/profile.html', context)


 