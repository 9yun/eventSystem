from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.urls import reverse
#from django.contrib.auth import views as auth_views
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User as auth_user
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db.utils import IntegrityError
from django.db.models import DateTimeField
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from django.utils import timezone

from django.forms import formset_factory

from .models import User, Event, Question, Choice, Response, OpenResponse, ChoiceResponse, EventForm, QuestionForm, ChoiceForm, OpenResponseForm, ChoiceResponseForm



MIN_PASSWORD_LENGTH = 6

@login_required
def index(request):
    return HttpResponse("Greetings! This will soon be an events RSVP app :)")

def user_reg(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        if len(password) < MIN_PASSWORD_LENGTH:
            print("Password too short!")
            messages.error(request, "Password is too short! For your own safety, please pick a stronger password.")
            return redirect('user_reg')
        try:
            newUser = auth_user.objects.create_user(username, email, password)
            validate_email(email)
            newUser.save()
            user = authenticate(username = username, password = password)
            login(request, user)
            print("Success!")
            return redirect('user_home', username=username)
        except ValidationError: #Invalid Email
            print("Invalid Email!")
            messages.error(request, "Invalid Email! Please try again with a different email!")
            return redirect('user_reg')
        except IntegrityError: #Username already exists
            print("Username exists!")
            messages.error(request, "Sorry, that username is taken. Please try again with a different username!")
            return redirect('user_reg')
        except ValueError: #Blank Username
            messages.error(request, "All fields have to be non-empty")
            return redirect('user_reg')
        #return redirect('user_home', username=username)
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
            return redirect('user_home', username=username)
        else:
            messages.error(request, "Invalid credentials")
            return redirect(user_login)
    else:
        print("GET request detected!")
        return render(request, 'eventSystem/login.html', {})

@login_required
def user_logout(request):
    logout(request) # TO-DO: Check if user was logged-in in the first place?
    return redirect(user_login)
    
@login_required
def login_redirect(request):
    nextUrl = request.GET.get('next')
    print("Next URL: " + nextUrl)
    #return redirect(nextUrl)
    return HttpResponse(nextUrl)

@login_required    
def user_home(request, username):
    # Retrieve user from DB
    userQueryResult = User.objects.filter(username=username)
    if len(userQueryResult) == 0:
        print("Unable to find user %s"%username)
        # Initialize User object
        foundUser = User(username = username, email = request.user.email)
        foundUser.save()
        #return HttpResponse("Who are you %s? You must be a new user..."%username)
    else:
        foundUser = userQueryResult[0]
    owned_events = foundUser.isOwnerOf()
    vendor_events = foundUser.isVendorOf()
    guest_events = foundUser.isGuestOf()
    owns_events = len(owned_events) > 0
    has_vendor_events = len(vendor_events) > 0
    has_guest_events = len(guest_events) > 0
    noun = "You" if request.user.username == username else username
    context = {'user' : foundUser, 'owned_events' : owned_events, 'owns_events': owns_events, 'vendor_events': vendor_events, 'guest_events': guest_events, 'has_vendor_events' : has_vendor_events, 'has_guest_events' : has_guest_events, 'noun':noun}
    return render(request, 'eventSystem/user_home.html', context)

@login_required # TO-DO: Also need to enforce either owner or vendor?
# This view is only meant to be accessible to owner of that event
def event_home(request, eventname):
    if not user_owns_event(request, eventname):
        return HttpResponse(content="401 Unauthorized", status=401, reason="Unauthorized")
    event = Event.objects.filter(eventname=eventname)[0] # Safe to do it here since checks were made above for 404
    event_owners = event.getOwners()
    event_vendors = event.getVendors()
    event_guests = event.getGuests()
    has_vendors = len(event_vendors) > 0
    has_guests = len(event_guests) > 0
    context = {'event_name' : event.eventname, 'event_date' : event.date, 'event_start' : event.start_time, 'event_end': event.end_time,  'event_owners' : event_owners, 'event_vendors' : event_vendors, 'event_guests' : event_guests, 'has_vendors' : has_vendors, 'has_guests' : has_guests}
    
    return render(request, 'eventSystem/event_home.html', context)

@login_required
def create_event(request, username):
    if request.method == "POST":
        print("Post detected to event creation")
        print("Post body received: " + str(request.POST))
        newEventForm = EventForm(request.POST)
        if not newEventForm.is_valid():
            print("Invalid event!")
            print(newEventForm.errors)
            messages.error(request, "Invalid Event! Please try different event name and enter date in valid format such as MM/DD/YY HH:MM:SS")
            return redirect(create_event, username=username)
        print("Valid event!")
        creator = User.objects.filter(username = username)[0] # Safe to assume at this point that a user will be found since login_required decorator has been enforced
        newEvent = newEventForm.save()
        print("Saved event!")
        newEvent.addOwner(creator) # Creator is a de-facto owner
        print("Owners of new event: " + str(newEvent.getOwners()))
        print("Vendors of new event: " + str(newEvent.getVendors()))
        print("Guests of new event: " + str(newEvent.getGuests()))
        return redirect(user_home, username=username)
    else:
        form = EventForm({})
        context = {'username' : username, 'form': form}
        return render(request, 'eventSystem/create_event.html', context)

@login_required
def view_questions(request, eventname):
    # Must verify that request.user is either in event.owners OR event.vendors
       # if not in owners and in vendors, then can still view all questions but can only view selected responses?
    if not (user_owns_event(request, eventname) or user_vendor_for_event(request, username)):
        return HttpResponse(content="401 Unauthorized", status=401, reason="Unauthorized")
    # Event existence and verification of permissions done at this point
    event = Event.objects.filter(eventname = eventname)[0]# Can assume at this point that event exists in DB, since checks were made above for 404
    event_name = event.eventname
    #date_time = event.date_time
    date = event.date
    start = event.start_time
    end = event.end_time
    questions = event.question_set.all()
    has_questions = len(questions) > 0
    qnData = []
    for index in range(len(questions)):
        qnData.append((questions[index], [choice.choice_text for choice in questions[index].choice_set.all()]))
    visible_to = [vendor.username for question in questions for vendor in  question.visible_to.all()]
    context = {'event_name': event_name, 'event_date': date, 'event_start' : start, 'event_end': end, 'questions': qnData, 'has_questions': has_questions, 'visible_to': visible_to}
    return render(request, 'eventSystem/view_questions.html', context)

@login_required
def add_questions(request, eventname):
    # must be owner of event, not even guest
    if not user_owns_event(request, eventname):
        return HttpResponse(content="401 Unauthorized", status=401, reason="Unauthorized")
    event = Event.objects.filter(eventname = eventname)[0]# Can assume at this point that event exists in DB, since checks were made above for 404  
    if request.method == "POST":
        # TO-DO : save qns to db... All validation already done on client side?
        # TO-DO : Iterate through request.POST["questions"], and for each qn, save qn to db with qnText field, then look at qnType field and construct Choice object for saved qn if necessary
        print("Saving of questions suceeded!")
        return redirect(view_questions, eventname=eventname)

    else:
        # Any contextual information needed?
        event_name = event.eventname
        #date_time = event.date_time
        date = event.date
        start = event.start_time
        end = event.end_time
        questions = event.question_set.all()
        has_questions = len(questions) > 0
        context = {'event_name': event_name, 'event_date': date, 'event_start': start, 'event_end': end, 'questions': questions, 'has_questions': has_questions}                
        return render(request, 'eventSystem/add_questions.html', context)

def modify_questions(request, eventname):
    # must be owner of event, not even guest
    if not user_owns_event(request, eventname):
        return HttpResponse(content="401 Unauthorized", status=401, reason="Unauthorized")
    event = Event.objects.filter(eventname = eventname)[0]# Can assume at this point that event exists in DB, since checks were made above for 404 
    event_name = event.eventname
    #date_time = event.date_time
    date = event.date
    start = event.start_time
    end = event.end_time
    questions = event.question_set.all()
    has_questions = len(questions) > 0
    question_choices = []
    qn_formset_factory = formset_factory(QuestionForm, extra=2)
    formset = [QuestionForm(instance = question) for question in questions]
    questions_initial_formset = qn_formset_factory(initial=formset)
                                    
    if request.method == "POST":
        # TO-DO : Iterate through request.POST["questions"], and for each qn, save qn to db with qnText field, then look at qnType field and construct Choice object for saved qn if necessary
        postData = request.POST
        
        #qns_modified = postData['questions']

        # Keep track of what's modified and what's new
        #submitted_formset = qn_formst_factory(request.POSTinitial=formset)
        
        choices_modified = choiceData['choices']
        print("Saving of questions suceeded!")
        return redirect(view_questions, eventname=eventname)
    else:
        # Retrieve questions ... and display them through form?

        # REFACTOR TO USE FORMSET
        
        for index in range(len(questions)):
            question = questions[index]
            choices = question.choice_set.all()
            question_choices.append((QuestionForm(instance=question), question.pk, [(ChoiceForm(instance=choice), choice.pk) for choice in choices]))
        questions_formset = [formset_factory(QuestionForm(instance = question)) for question in questions]
        question_data = (questions_formset, question_choices)
        context = {'event_name': event_name, 'event_date': date, 'event_start': start, 'event_end': end, 'questions': question_choices}
        #context = {'event_name': event_name, 'date': date, 'start' : start, 'end': end, 'formset': questions_formset, 'questions' : question_choices}
        return render(request, 'eventSystem/modify_questions.html', context)
    
    # For adding/removing questions and users to event
def modify_event(request, eventname):
    if not user_owns_event(request, eventname):
        return HttpResponse(content="401 Unauthorized", status=401, reason="Unauthorized")
    oldEvent = Event.objects.filter(eventname=eventname)[0] # Can assume at this point that event exists in DB, since checks were made above for 404 
    if request.method == "POST":
        # Convert names into user objects
        print("POST info received: " + str(request.POST))
        modEventForm = EventForm(request.POST, instance=oldEvent)

        if not modEventForm.is_valid():
            print("GG form still not valid liao")
            print(modEventForm.errors)
            messages.warning(request, "Invalid input")
            return redirect(modify_event, eventname=eventname)

        print("Valid modification!")
        oldEvent.save()
        return redirect(event_home, eventname=eventname)
    else:
        changeForm = EventForm(instance=oldEvent)
        context = {'event' : oldEvent, 'form' : changeForm, 'user' : request.user}
        return render(request, 'eventSystem/modify_event.html', context)


# Helper function used by event_home and modify_event
def user_owns_event(request, eventname):
    eventSet = Event.objects.filter(eventname = eventname)
    if len(eventSet) == 0:
        raise Http404("Event does not exist")
    event = eventSet[0]
    event_owners = event.getOwners()
    event_owners_names = [owner.username for owner in event_owners]
    print("Owners: " + str(event_owners_names))
    return request.user.username in event_owners_names # If user is not owner of this event, cannot view its homepage, only other pages like guest view or vendor view of event

def user_vendor_for_event(request, eventname):
    eventSet = Event.objects.filter(eventname = eventname)
    if len(eventSet) == 0:
        raise Http404("Event does not exist")
    event = eventSet[0]
    event_vendors = event.getVendors()
    event_vendors_names = [vendor.username for vendor in event_vendors]
    print("Vendors: " + str(event_vendors_names))
    return request.user.username in event_vendors_names

# Inefficient to serve files with django :(
def get_script(request, script_path):
    with open(script_path,'r') as f:
        data = f.read()
        response = HttpResponse(data, content_type='text/javascript')
        response['Content-Length'] = len(data)
    return response
                                        


def get_modify_qns_script(request):
    return get_script(request, "./eventSystem/static/questions/js/modify_questions.js")

def get_add_qns_script(request):
    return get_script(request, "./eventSystem/static/questions/js/question.js")
    
