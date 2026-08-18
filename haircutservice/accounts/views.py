import logging
import random

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.shortcuts import redirect, render, get_object_or_404
from shopkeeper.models import QueueEntry, Salon, SiderImage

from .models import CustomUser

User = get_user_model()
logger = logging.getLogger(__name__)


def _generate_otp():
    return str(random.randint(100000, 999999))


def _send_otp_email(request, to_email, subject, message):
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [to_email], fail_silently=False)
        return True, None
    except Exception as exc:
        logger.exception('OTP email could not be sent to %s', to_email)
        request.session['email_delivery_error'] = str(exc)
        return False, str(exc)


def _clear_signup_session(request):
    request.session.pop('pending_signup', None)
    request.session.pop('signup_verification_otp', None)
    request.session.pop('signup_welcome_otp', None)
    request.session.pop('signup_step', None)


def _clear_reset_password_session(request):
    request.session.pop('reset_password_email', None)
    request.session.pop('reset_password_otp', None)
    request.session.pop('reset_password_step', None)


def SignUp(request):
    if request.method == 'POST':
        if 'otp' in request.POST:
            return verify_otp(request)

        username = (request.POST.get('username') or '').strip()
        name = (request.POST.get('name') or '').strip()
        mobile = (request.POST.get('mobile') or '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        role = request.POST.get('role')
        email = (request.POST.get('email') or '').strip()

        if not email:
            messages.error(request, 'Email is required.')
            return redirect(request.META.get('HTTP_REFERER', 'home'))

        if len(mobile) != 10 or not mobile.isdigit():
            messages.error(request, 'Phone number must be 10 digits.')
            return redirect(request.META.get('HTTP_REFERER', 'home'))

        if password != confirm_password:
            messages.error(request, 'Passwords do not match. Please try again.')
            return redirect(request.META.get('HTTP_REFERER', 'home'))

        if User.objects.filter(username=username).exists():
            messages.error(request, f"Username '{username}' is already taken. Please choose another one.")
            return redirect(request.META.get('HTTP_REFERER', 'home'))

        if User.objects.filter(email=email).exists():
            messages.error(request, f"Email '{email}' is already registered.")
            return redirect(request.META.get('HTTP_REFERER', 'home'))

        pending_signup = {
            'username': username,
            'name': name,
            'mobile': mobile,
            'password': password,
            'role': role,
            'email': email,
        }
        verification_otp = _generate_otp()
        request.session['pending_signup'] = pending_signup
        request.session['signup_verification_otp'] = verification_otp
        request.session['signup_step'] = 'verify_email'

        email_sent, email_error = _send_otp_email(
            request,
            email,
            'Email verification OTP',
            f'Hello {name or username},\n\nYour email verification OTP: {verification_otp}\n\nUse it to verify your email address.',
        )

        return render(request, 'accounts/signup.html', {
            'message': 'Enter the email verification OTP',
            'email': email,
            'otp_stage': 'verify_email',
            'email_sent': email_sent,
            'email_error': email_error,
            'debug_otp': None,
        })

    return render(request, 'accounts/signup.html', {'otp_stage': 'signup'})


def verify_otp(request):
    if request.method != 'POST':
        return redirect('home')

    pending_signup = request.session.get('pending_signup')
    if not pending_signup:
        messages.error(request, 'Signup session expired. Please try again.')
        return redirect('home')

    otp_value = (request.POST.get('otp') or '').strip()
    step = request.session.get('signup_step')

    if step == 'verify_email':
        expected_otp = request.session.get('signup_verification_otp')
        if otp_value != expected_otp:
            return render(request, 'accounts/signup.html', {
                'message': 'Invalid email verification OTP. Please try again.',
                'email': pending_signup['email'],
                'otp_stage': 'verify_email',
            })

        user = User.objects.create_user(
            username=pending_signup['username'],
            email=pending_signup['email'],
            password=pending_signup['password'],
            name=pending_signup['name'],
            mobile=pending_signup['mobile'],
            is_customer=pending_signup['role'] == 'customer',
            is_shopkeeper=pending_signup['role'] == 'shopkeeper',
        )
        _clear_signup_session(request)
        auth_login(request, user)
        messages.success(request, f'Welcome {user.username}! Your account has been created.')
        return redirect('home')

    messages.error(request, 'Signup flow is invalid.')
    return redirect('home')


def login(request):
    if request.method == "POST":
        email = (request.POST.get('email') or '').strip()
        password = request.POST.get('password', '')

        user = None
        if email:
            account = User.objects.filter(email__iexact=email).first()
            if account:
                user = authenticate(request, username=account.username, password=password)

        if user is not None:
            auth_login(request, user)
            messages.success(request, f"Welcome {user.username}!")
            return redirect('home')
        else:
            messages.error(request, "Invalid email or password. Please try again.")
            return redirect('home')

    all_salons = Salon.objects.all()
    has_salon = False
    if request.user.is_authenticated:
        has_salon = Salon.objects.filter(owner=request.user).exists()

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


def forgot_password(request):
    if request.user.is_authenticated:
        return redirect('home')
 
    if request.method == 'POST':
        email = (request.POST.get('email') or '').strip()
        if not email:
            messages.error(request, 'Email is required.')
            return render(request, 'accounts/forgot_password.html')
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, 'No user is registered with this email address.')
            return render(request, 'accounts/forgot_password.html')
 
        otp = _generate_otp()
        request.session['reset_password_email'] = user.email
        request.session['reset_password_otp'] = otp
        request.session['reset_password_step'] = 'verify_otp'
 
        email_sent, email_error = _send_otp_email(
            request,
            user.email,
            'Password Reset OTP',
            f'Hello {user.username},\n\nYour password reset OTP is: {otp}\n\nUse it to reset your password.',
        )
 
        if not email_sent:
            messages.error(request, f'Failed to send OTP email. {email_error or ""}')
            return render(request, 'accounts/forgot_password.html')
        messages.success(request, 'An OTP has been sent to your email address.')
        return redirect('verify_password_reset_otp')
 
    return render(request, 'accounts/forgot_password.html')


def verify_password_reset_otp(request):
    if request.session.get('reset_password_step') != 'verify_otp':
        messages.error(request, 'Invalid step. Please start the password reset process again.')
        return redirect('forgot_password')

    email = request.session.get('reset_password_email')
    if not email:
        messages.error(request, 'Session expired. Please try again.')
        return redirect('forgot_password')

    if request.method == 'POST':
        otp_value = (request.POST.get('otp') or '').strip()
        expected_otp = request.session.get('reset_password_otp')

        if otp_value != expected_otp:
            messages.error(request, 'Invalid OTP. Please try again.')
            return render(request, 'accounts/verify_reset_otp.html', {'email': email})

        request.session['reset_password_step'] = 'reset_form'
        return redirect('reset_password_confirm')

    return render(request, 'accounts/verify_reset_otp.html', {'email': email})


def reset_password_confirm(request):
    if request.session.get('reset_password_step') != 'reset_form':
        messages.error(request, 'Invalid step. Please start the password reset process again.')
        return redirect('forgot_password')

    email = request.session.get('reset_password_email')
    if not email:
        messages.error(request, 'Session expired. Please try again.')
        return redirect('forgot_password')

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        messages.error(request, 'An error occurred. User not found.')
        _clear_reset_password_session(request)
        return redirect('forgot_password')

    if request.method == 'POST':
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'accounts/reset_password_form.html')

        try:
            validate_password(password, user=user)
        except ValidationError as e:
            messages.error(request, list(e.messages))
            return render(request, 'accounts/reset_password_form.html')

        user.set_password(password)
        user.save()
        _clear_reset_password_session(request)
        messages.success(request, 'Your password has been reset successfully. Please log in.')
        return redirect('login')

    return render(request, 'accounts/reset_password_form.html')

@login_required(login_url='login')
def logout_user (request):
    logout(request)
    messages.info(request, "you have  been logged out")
    return redirect('login')

@login_required
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
