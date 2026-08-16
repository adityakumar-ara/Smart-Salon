import random
import secrets

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.shortcuts import redirect, render, get_object_or_404
from django.utils import timezone
from shopkeeper.models import QueueEntry, Salon, SiderImage

from .models import CustomUser

User = get_user_model()
PASSWORD_RESET_OTP_LIFETIME_SECONDS = 10 * 60


def _generate_otp():
    return str(random.randint(100000, 999999))


def _send_otp_email(request, to_email, subject, message):
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [to_email], fail_silently=False)
        return True, None
    except Exception as exc:
        request.session['email_delivery_error'] = str(exc)
        return False, str(exc)


def _clear_signup_session(request):
    request.session.pop('pending_signup', None)
    request.session.pop('signup_verification_otp', None)
    request.session.pop('signup_welcome_otp', None)
    request.session.pop('signup_step', None)


def _clear_password_reset_session(request):
    for key in ('password_reset_user_id', 'password_reset_email', 'password_reset_otp',
                'password_reset_otp_created_at', 'password_reset_verified'):
        request.session.pop(key, None)


def forgot_password(request):
    if request.method == 'POST':
        email = (request.POST.get('email') or '').strip()
        user = User.objects.filter(email__iexact=email).first()
        if not user:
            messages.error(request, 'No account is registered with this email address.')
            return render(request, 'accounts/forgot_password.html', {'email': email})

        otp = _generate_otp()
        request.session['password_reset_user_id'] = user.pk
        request.session['password_reset_email'] = user.email
        request.session['password_reset_otp'] = otp
        request.session['password_reset_otp_created_at'] = timezone.now().timestamp()
        request.session['password_reset_verified'] = False
        email_sent, _ = _send_otp_email(
            request, user.email, 'Password reset OTP',
            f'Hello {user.name or user.username},\n\nYour password reset OTP is: {otp}\n\nIt expires in 10 minutes. Do not share this code with anyone.',
        )
        if not email_sent:
            _clear_password_reset_session(request)
            messages.error(request, 'We could not send the OTP. Please try again later.')
            return render(request, 'accounts/forgot_password.html', {'email': email})
        return redirect('verify_password_reset_otp')
    return render(request, 'accounts/forgot_password.html')


def verify_password_reset_otp(request):
    user_id = request.session.get('password_reset_user_id')
    email = request.session.get('password_reset_email')
    expected_otp = request.session.get('password_reset_otp')
    created_at = request.session.get('password_reset_otp_created_at')
    if not all([user_id, email, expected_otp, created_at]):
        messages.error(request, 'Your password reset session has expired. Please request a new OTP.')
        return redirect('forgot_password')
    if timezone.now().timestamp() - float(created_at) > PASSWORD_RESET_OTP_LIFETIME_SECONDS:
        _clear_password_reset_session(request)
        messages.error(request, 'This OTP has expired. Please request a new one.')
        return redirect('forgot_password')
    if request.method == 'POST':
        otp = (request.POST.get('otp') or '').strip()
        if not secrets.compare_digest(otp, expected_otp):
            messages.error(request, 'The OTP is invalid. Please try again.')
            return render(request, 'accounts/verify_reset_otp.html', {'email': email})
        request.session['password_reset_verified'] = True
        request.session.pop('password_reset_otp', None)
        return redirect('reset_password_confirm')
    return render(request, 'accounts/verify_reset_otp.html', {'email': email})


def reset_password_confirm(request):
    user_id = request.session.get('password_reset_user_id')
    if not user_id or not request.session.get('password_reset_verified'):
        messages.error(request, 'Verify your OTP before changing your password.')
        return redirect('forgot_password')
    user = User.objects.filter(pk=user_id).first()
    if not user:
        _clear_password_reset_session(request)
        messages.error(request, 'Account not found. Please request a new OTP.')
        return redirect('forgot_password')
    if request.method == 'POST':
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'accounts/reset_password_form.html')
        try:
            validate_password(password, user)
        except ValidationError as error:
            for message in error.messages:
                messages.error(request, message)
            return render(request, 'accounts/reset_password_form.html')
        user.set_password(password)
        user.save(update_fields=['password'])
        _clear_password_reset_session(request)
        messages.success(request, 'Your password has been reset. Please log in.')
        return redirect('login')
    return render(request, 'accounts/reset_password_form.html')


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
            'debug_otp': verification_otp if not email_sent else None,
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

        welcome_otp = _generate_otp()
        request.session['signup_welcome_otp'] = welcome_otp
        request.session['signup_step'] = 'welcome'
        email_sent, email_error = _send_otp_email(
            request,
            pending_signup['email'],
            'Welcome OTP',
            f'Hello {pending_signup["name"] or pending_signup["username"]},\n\nWelcome OTP: {welcome_otp}\n\nUse it to complete your signup.',
        )
        return render(request, 'accounts/signup.html', {
            'message': 'Welcome OTP',
            'email': pending_signup['email'],
            'otp_stage': 'welcome',
            'email_sent': email_sent,
            'email_error': email_error,
            'debug_otp': welcome_otp if not email_sent else None,
        })

    if step == 'welcome':
        expected_otp = request.session.get('signup_welcome_otp')
        if otp_value != expected_otp:
            return render(request, 'accounts/signup.html', {
                'message': 'Invalid welcome OTP. Please try again.',
                'email': pending_signup['email'],
                'otp_stage': 'welcome',
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
