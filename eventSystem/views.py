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

#from django.forms import formset_factory
from django.forms import modelform_factory, modelformset_factory
from .models import User, Event, Question, Choice, Response, OpenResponse, ChoiceResponse, EventForm, QuestionForm, ChoiceForm, OpenResponseForm, ChoiceResponseForm, VisibleToVendorField

from django.http import JsonResponse


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
def create_event(request):
    # safe to assume request.user exists because of @login_required decorator?
    username = request.user.username
    if request.method == "POST":
        print("Post detected to event creation")
        print("Post body received: " + str(request.POST))
        newEventForm = EventForm(request.POST)
        if not newEventForm.is_valid():
            print("Invalid event!")
            print(newEventForm.errors)
            messages.error(request, "Invalid Event! Please try different event name and enter date in valid format such as MM/DD/YY HH:MM:SS")
            return redirect(create_event)
        print("Valid event!")
        creator = User.objects.filter(username = username)[0] # Safe to assume at this point that a user will be found since login_required decorator has been enforced
        newEvent = newEventForm.save()
        print("Saved event!")
        newEvent.addOwner(creator) # Creator is a de-facto owner
        print("Owners of new event: " + str(newEvent.getOwners()))
        print("Vendors of new event: " + str(newEvent.getVendors()))
        print("Guests of new event: " + str(newEvent.getGuests()))
        return HttpResponse(status = 200) 
    else:
        #form = EventForm({})
        form = EventForm()
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
        qnData.append((questions[index], [choice.choice_text for choice in questions[index].choice_set.all()], [vendor.username for vendor in questions[index].visible_to.all()]))
    #visible_to = [vendor.username for question in questions for vendor in  question.visible_to.all()]
    context = {'event_name': event_name, 'event_date': date, 'event_start' : start, 'event_end': end, 'questions': qnData, 'has_questions': has_questions}
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
        print("POST body: " + str(request.POST))
        new_qn_form = QuestionForm(request.POST)
        if not new_qn_form.is_valid():
            print("Form is invalid!")
            print(new_qn_form.errors)
            messages.error(request, "Invalid Question! Please ensure text is properly filled.")
            return redirect(create_event, eventname=eventname)
        #print("Saving of questions suceeded!")
        new_qn = new_qn_form.save(commit=False)
        new_qn.event_for = event
        new_qn.save()
        new_qn_form.save_m2m() #need to do this to register foreign-key relationships into DB 
        print("Saving of questions suceeded!") 
        return redirect(view_questions, eventname=eventname)

    else:
        # Any contextual informatnion needed?
        event_name = event.eventname
        #date_time = event.date_time
        date = event.date
        start = event.start_time
        end = event.end_time
        questions = event.question_set.all()
        has_questions = len(questions) > 0
        QuestionFactory = modelform_factory(Question, fields = ('qn_text', 'visible_to'))
        new_qn_form = QuestionFactory()
        # Limit QuerySet
        new_qn_form.fields['visible_to'] = VisibleToVendorField(queryset = None, event = event)
        context = {'event_name': event_name, 'event_date': date, 'event_start': start, 'event_end': end, 'questions': questions, 'has_questions': has_questions, 'new_qn_form': new_qn_form}                
        return render(request, 'eventSystem/add_questions.html', context)
    
def modify_questions(request, eventname):
    # must be owner of event, not even guest
    if not user_owns_event(request, eventname):
        return HttpResponse(content="401 Unauthorized", status=401, reason="Unauthorized")
    event = Event.objects.filter(eventname = eventname)[0]# Can assume at this point that event exists in DB, since checks were made above for 404 
    event_name = event.eventname
    date = event.date
    start = event.start_time
    end = event.end_time
    questions = event.question_set.all().order_by('pk')
    has_questions = len(questions) > 0
    question_choices = []
    qn_formset = modelformset_factory(Question, fields = ('qn_text', 'visible_to'), extra=0)
    initial_forms = Question.objects.filter(event_for = event).order_by('pk')
    formset = qn_formset(queryset = initial_forms, prefix = 'questions')
    choice_formset = modelformset_factory(Choice, fields = ('choice_text',), extra=0)
    initial_choices_forms = [Choice.objects.filter(qn_for=questions[index]) for index in range(len(questions))]
    c_formsets = [choice_formset(queryset = initial_choices_forms[index], prefix = 'choices-' + str(index)) for index in range(len(questions))]
    all_formsets = [(formset[qn_index], c_formsets[qn_index]) for qn_index in range(len(formset))]
    formset_management = formset.management_form
    
    if request.method == "POST":

        print("Massive post body: " + str(request.POST))
        # Keep track of what's modified and what's new
        # 1) Validation of qn_text and visible_to fields
        submitted_formset = qn_formset(request.POST, initial=initial_forms, prefix = 'questions')
        if submitted_formset.is_valid():
            print("Saving of modified questions suceeded!")
            # Save questions
            submitted_formset.save()
            print("About to validate and save questions")
            for choice_formset_index in range(len(c_formsets)):
                submitted_choice_formset = choice_formset(request.POST, initial=initial_choices_forms[choice_formset_index], prefix = 'choices-' + str(choice_formset_index))
                if not submitted_choice_formset.is_valid():
                    print("Errors in choice form " + str(choice_formset_index))
                    [print(form_errors) for form_errors in submitted_choice_formset.errors]
                    return redirect(modify_questions, eventname=eventname)
                # Save modified choices of question
                modified_choices = submitted_choice_formset.save(commit=False)
                print("Length of submitted choices formset: " + str(len(submitted_choice_formset)))
                print("Length of modified choices: " + str(len(modified_choices)))
                for modified_choice_index in range(len(submitted_choice_formset)):
                    modified_choice = submitted_choice_formset[modified_choice_index]
                    modified_choice.qn_for = questions[choice_formset_index]
                    modified_choice.save() # save back to update foreign-key relations with qn object
                print("Saved choices for question " + str(choice_formset_index))
            print("Saving of modified choices succeeded!")
            return redirect(view_questions, eventname=eventname)
        
        print("Errors in question forms: ")
        [print(form_errors) for form_errors in submitted_formset.errors]
        # Add error message
        return redirect(modify_questions, eventname=eventname)
    else:
        # Retrieve questions ... and display them through form?
        # REFACTOR TO USE FORMSET
        context = {'event_name': event_name, 'event_date': date, 'event_start': start, 'event_end': end, 'formset': all_formsets, 'formset_management': formset_management}
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
        #oldEvent.save()
        modEventForm.save()
        return redirect(event_home, eventname=eventname)
    else:
        changeForm = EventForm(instance=oldEvent)
        [print(field.name, field) for field in changeForm]
        context = {'event' : oldEvent, 'form' : changeForm, 'user' : request.user}
        return render(request, 'eventSystem/modify_event.html', context)

@login_required    
def add_qn_new_event(request):
    if not hasattr(request, 'user') or not hasattr(request.user, 'username'):
        print("Rejecting request from unknown user")
        return HttpResponse(content="You are not a registered and logged-in user", status=401, reason="Unauthorized")
                                    
    if request.method != "POST":
        return HttpResponse(content="This URL is for POST requests only.", status=200)

    user_ordered_events = Event.adi.owners.all().order_by('pk')
    if len(user_ordered_events) == 0:
        print("User has not created any events yet.")
        return HttpResponse(content="No event found for this user", status = 404, reason = "You have no events")
    user_latest_event = user_ordered_events[len(user_ordered_events) - 1] # query sets don't allow the -1 indexing for some reason        
    print("Event name : %s"%user_latest_event.eventname)

    # validate qns, save with commit=false
    #errors = []
    valid_qns = []
    print("Post data: " + str(request.POST))
    for new_qn_json in request.POST:
        new_qn_form = QuestionForm(new_qn_json)
        if new_qn_form.is_valid() :
            new_qn = new_qn_form.save(commit=False)
            # set event of qns to this event     
            new_qn.event_for = user_latest_event
            valid_qns.append(new_qn)
        else:
            return HttpResponse(content="Invalid question detected. Not saving. Cause for rejection: %s"%new_qn_form.errors, status=200)
    # Save to DB
    if len(valid_qns) > 0:
        for valid_qn in valid_qns:
            valid_qn.save() 
            print("Saved question %s", valid_qn.qn_text)
    user_home_url = "/eventSystem/user/%s"%request.user
    print("Saved all questions, about to redirect user to his home page %s"%user_home_url)
    return JsonResponse({'redirect_to':user_home_url})
    

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

