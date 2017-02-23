from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect, Http404
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
            #return HttpResponse("Booya! Login success!")
            return redirect('user_home', username=username) 
        else:
            return HttpResponse("Dang! Login failed!") # TO-DO: Replace with in-line error message in template?
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
    owned_events = foundUser.isOwnerOf()
    vendor_events = foundUser.isVendorOf()
    guest_events = foundUser.isGuestOf()
    owns_events = len(owned_events) > 0
    has_vendor_events = len(vendor_events) > 0
    has_guest_events = len(guest_events) > 0
    #print("User's events: " + str(owned_events))
    context = {'user' : foundUser, 'owned_events' : owned_events, 'owns_events': owns_events, 'has_vendor_events' : has_vendor_events, 'has_guest_events' : has_guest_events}
    return render(request, 'eventSystem/user_home.html', context)

@login_required # TO-DO: Also need to enforce either owner or vendor?
def event_home(request, eventname):
    eventSet = Event.objects.filter(eventname = eventname)
    if len(eventSet) == 0:
        raise Http404("Event does not exist")
    event = eventSet[0]
    event_owners = event.getOwners()
    event_vendors = event.getVendors()
    event_guests = event.getGuests()
    has_vendors = len(event_vendors) > 0
    has_guests = len(event_guests) > 0
    context = {'event_name' : event.eventname, 'date_time' : event.date_time,  'event_owners' : event_owners, 'event_vendors' : event_vendors, 'event_guests' : event_guests, 'has_vendors' : has_vendors, 'has_guests' : has_guests}
    return render(request, 'eventSystem/event_home.html', context)
