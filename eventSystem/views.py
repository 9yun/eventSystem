from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth import views as auth_views
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User as auth_user
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db.utils import IntegrityError
from django.contrib.auth.decorators import login_required

from .models import User, Event

# Create your views here.

@login_required
def index(request):
    return HttpResponse("Greetings! This will soon be an events RSVP app :)")

def user_reg(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        try:
            newUser = auth_user.objects.create_user(username, email, password)
            validate_email(email)
            newUser.save()
            print("Success!")
        except ValidationError: #Invalid Email
            print("Invalid Email!")
            return HttpResponse("Invalid Email! Please try again with a different email!")
        except IntegrityError: #Username already exists
            print("Username exists!")
            return HttpResponse("Sorry, that username is taken. Please try again with a different username!")
        return redirect('user_home', username=username)
    else:
        return render(request, 'eventSystem/register.html', {})
            
            
def user_login(request):
    if request.method == 'POST':
        print("POST request detected!")
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username = username, password = password)
        if user is not None:
            login(request, user) # sets User ID in session
            print("Request object: " + str(request))
            return HttpResponse("Booya! Login success!")
        else:
            return HttpResponse("Dang! Login failed!")
    else:
        print("GET request detected!")
        return render(request, 'eventSystem/login.html', {})

    # Enforce login_required decorator

@login_required    
def user_home(request, username):
    # Retrieve user from DB
    userQueryResult = User.objects.filter(username=username)
    if len(userQueryResult) == 0:
        print("Unable to find user %s"%username)
        return HttpResponse("Who are you %s? You must be a new user..."%username)
    foundUser = userQueryResult[0]
    eventNames = [e.eventname for e in foundUser.isOwnerOf()]
    [print(e.eventname) for e in foundUser.isOwnerOf()]
    #print("User's events: " + str(eventNames))
    return HttpResponse("Welcome back %s!"%username)
