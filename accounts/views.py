from email.message import EmailMessage
from django.shortcuts import render,redirect,HttpResponse
from django.contrib import messages
from accounts.forms import RegisterForm
from accounts.models import Account
from django.contrib.auth import authenticate,login as Login,logout as Logout
from django.contrib.auth.decorators import login_required
# Create your views here.
#Verification Email import
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_decode,urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage


def register(request):
    if request.method=="POST":
        form =RegisterForm(request.POST)
        print(form,"ALL OK")
        if form.is_valid:
            first_name=form.cleaned_data['first_name']
            last_name=form.cleaned_data['last_name']
            email=form.cleaned_data['email']
            phone_number=form.cleaned_data['phone_number']
            password=form.cleaned_data['password']
            username=email.split("@")[0]

            user=Account.objects.create_user(first_name=first_name,last_name=last_name,username=username,email=email,password=password)
            user.phone_number=phone_number
            user.save()

            #USER ACTIVATION
            current_site=get_current_site(request)
            mail_subject="Please activate your account"
            message=render_to_string("accounts/account_verification_email.html",{
                'user':user,
                'domain':current_site,
                'uid':urlsafe_base64_encode(force_bytes(user.pk)),
                'token':default_token_generator.make_token(user),
            })
            to_email=email
            send_email=EmailMessage(mail_subject,message,to=[to_email])
            send_email.send()
            # messages.success(request,'Register Successfully')
            return redirect('accounts/login/?command-verification&email-'+email)
    else:
        form = RegisterForm()    
        print("RUUNNING REGIRSTER FORM")
    context={
        'form':form,
    }
    return render(request,'accounts/register.html',context)
def login(request):
    if request.method=="POST":
        email=request.POST['email']
        password=request.POST['password']

        user=authenticate(email=email,password=password)
        if user is not None:
            Login(request,user)
            messages.success(request,"You are now logged in.")
            return redirect("dashboard")
        else:
            messages.error(request,'Invalid login credentials')
            return redirect('login')
    return render(request,'accounts/login.html')
@login_required(login_url='login')
def logout(request):
    Logout(request)
    messages.success(request,"You are logged Out")
    return redirect('login')

def activate(request,uidb64,token):
    try:
        uid=urlsafe_base64_decode(uidb64).decode()
        user=Account._default_manager.get(pk=uid)
    except(TypeError,ValueError,OverflowError,Account.DoesNotExist):
        user=None
    
    if user is not None and default_token_generator.check_token(user,token):
        user.is_active=True
        user.save()
        messages.success(request,"Congrations ,Your account is activated")
        return redirect('login')
    else:
        messages.error(request,"Invalid activation link")
        return redirect('register')

def dashboard(request):
    return render(request,'accounts/dashboard.html')

def forgotPassword(request):
    if request.method=="POST":
        email=request.POST['email']
        if Account.objects.filter(email=email).exists():
            user=Account.objects.get(email__exact=email)
            #USER ACTIVATION
            current_site=get_current_site(request)
            mail_subject="Reset Your password"
            message=render_to_string("accounts/reset_password_email.html",{
                'user':user,
                'domain':current_site,
                'uid':urlsafe_base64_encode(force_bytes(user.pk)),
                'token':default_token_generator.make_token(user),
            })
            to_email=email
            send_email=EmailMessage(mail_subject,message,to=[to_email])
            send_email.send()
            messages.success(request,"Password reset mail has been sent to your email address")
            return redirect("login")
        else:
            messages.error(request,"Account does not exists")
            return redirect("forgotpassword")
    return render(request,"accounts/forgotpassword.html")

def resetpassword_validate(request,uidb64,token):
    try:
        uid=urlsafe_base64_decode(uidb64).decode()
        user=Account._default_manager.get(pk=uid)
    except(TypeError,ValueError,OverflowError,Account.DoesNotExist):
        user=None

    if user is not None and default_token_generator.check_token(user,token):
        request.session['uid']=uid
        messages.success(request,'please reset your password')
        return redirect("resetpassword")
    else:
        messages.error(request,"This link has been expired")
        return redirect('login')

def resetpassword(request):
    if request.method =="POST":
        password=request.POST['password']
        confirm_password=request.POST['confirm_password']

        if password == confirm_password:
            uid =request.session.get('uid')
            user=Account.objects.get(pk=uid)
            user.set_password(password)
            user.save()
            messages.success(request,'password reset successfull')
            return redirect("login")
        else:
            messages.error(request,'password does not match')
            return redirect('resetpassword')

    return render(request,'accounts/resetpassword.html')