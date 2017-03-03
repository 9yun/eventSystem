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
from django.core.mail import send_mail

from django.utils import timezone

#from django.forms import formset_factory
from django.forms import modelform_factory, modelformset_factory
from .models import User, Event, Question, Choice, Response, OpenResponse, ChoiceResponse, EventForm, QuestionForm, ChoiceForm, OpenResponseForm, ChoiceResponseForm, VisibleToVendorField, FinalizeForm

import json
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

'''
@login_required
def login_redirect(request):
    nextUrl = request.GET.get('next')
    print("Next URL: " + nextUrl)
    #return redirect(nextUrl)
    return HttpResponse(nextUrl)
'''

@login_required    
def user_home(request, username):
    # Verify that request user is same as user whose home page is requested
    if request.user.username != username:
        return HttpResponse(content="Sorry, you are not %s. Only the user himself can view his home page."%username, status=401, reason="Unauthorized")
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
    if not (user_owns_event(request, eventname) or user_vendor_for_event(request, eventname) or user_guest_for_event(request, eventname)):
        return HttpResponse(content="Sorry, you are unrelated to this event and therefore cannot view its questions", status=401, reason="Unauthorized")
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
        return HttpResponse(content="Sorry, only the owners can modify questions", status=401, reason="Unauthorized")
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

@login_required    
def modify_questions(request, eventname):
    # must be owner of event, not even guest
    if not user_owns_event(request, eventname):
        return HttpResponse(content="Sorry, only owners can modify questions", status=401, reason="Unauthorized")
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
    
    for qn_form in formset:
        qn_form.fields['visible_to'] = VisibleToVendorField(queryset = None, event = event)
        
    choice_formset = modelformset_factory(Choice, fields = ('choice_text',), extra=0)
    initial_choices_forms = [Choice.objects.filter(qn_for=questions[index]) for index in range(len(questions))]
    c_formsets = [choice_formset(queryset = initial_choices_forms[index], prefix = 'choices-' + str(index)) for index in range(len(questions))]
    all_formsets = [(formset[qn_index], c_formsets[qn_index]) for qn_index in range(len(formset))]
    formset_management = formset.management_form
    
    if request.method == "POST":

        # Keep track of what's modified and what's new
        # 1) Validation of qn_text and visible_to fields
        submitted_formset = qn_formset(request.POST, initial=initial_forms, prefix = 'questions')
        for form in submitted_formset:
            form.fields['visible_to'].required = False

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
                # Send a general email to update
                print("Length of submitted choices formset: " + str(len(submitted_choice_formset)))
                print("Length of modified choices: " + str(len(modified_choices)))
                to_send_email_set = []
                for modified_choice_index in range(len(submitted_choice_formset)):
                    modified_choice = submitted_choice_formset[modified_choice_index]
                    modified_choice.qn_for = questions[choice_formset_index]
                    for email in modified_choice.qn_for.get_responder_emails():
                        to_send_email_set.append(email)     
                    modified_choice.save() # save back to update foreign-key relations with qn object
                print("Saved choices for question " + str(choice_formset_index))
                # Send emails
                to_send_email_set = set(to_send_email_set)
                send_mail("Modified Questions for " + eventname, "The questions for " + eventname + " have been modified. Please login to update your responses!","eventSystem-" + eventname + "@eventUnlimited.ece590", list(to_send_email_set))
            print("Saving of modified choices succeeded!")
            return redirect(view_questions, eventname=eventname)
        
        print("Errors in question forms: ")
        errors_str = ""
        for form in submitted_forms:
            errors_str += form.errors + "\n"
            print(form.errors)
        messages.warning(request, errors_str)
        # Add error message
        return redirect(modify_questions, eventname=eventname)
    else:
        # Retrieve questions ... and display them through form?
        # REFACTOR TO USE FORMSET
        context = {'event_name': event_name, 'event_date': date, 'event_start': start, 'event_end': end, 'formset': all_formsets, 'formset_management': formset_management}
        return render(request, 'eventSystem/modify_questions.html', context)
    
    # For adding/removing questions and users to event
@login_required
def modify_event(request, eventname):
    if not user_owns_event(request, eventname):
        return HttpResponse(content="Sorry, only owners can modify the event", status=401, reason="Unauthorized")
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
def rsvp_event(request, eventname): # Can be used for both adding and updating responses
    if not user_guest_for_event(request, eventname):
        return HttpResponse(content="Sorry, you are not invited to this event.", status = 401, reason = "Unauthorized")
    # We now know user is invited
    user = User.objects.filter(username=request.user.username)[0]
    event = Event.objects.filter(eventname=eventname)[0]
    # Construct formset for responses with user's initial responses for this event
    current_user_openresponses = user.openresponse_set.all().filter(qn_for__event_for=event).order_by('pk') # OpenResponses filled by user for this event, in chronological order (Switch to qn order later if possible)
    current_user_choiceresponses = user.choiceresponse_set.all().filter(qn_for__event_for=event).order_by('pk') # Same, but for ChoiceResponses
    openresponse_formset_creator = modelformset_factory(OpenResponse, fields = ('response_value',), extra=0)
    openresponse_formset = openresponse_formset_creator(queryset = current_user_openresponses, prefix = 'open')
    choiceresponse_formset_creator = modelformset_factory(ChoiceResponse, fields= ('response_value',), extra=0)
    choiceresponse_formset = choiceresponse_formset_creator(queryset = current_user_choiceresponses, prefix = 'choice')
    all_formsets = [] #List of tuples, each tuple represents a question, first element of tuple is an openresponse, 2nd element is list of choice responses
    event_questions = event.question_set.all().order_by('pk')
    openresponse_index = 0
    choiceresponse_index = 0
    update = False
    openresponse_qns = [] # Used for setting of qn_for fields
    choiceresponse_qns = []
    choiceresponse_choices = []

    if len(current_user_choiceresponses) > 0 or len(current_user_openresponses) > 0: # submissions are only allowed for all event qns at a time, so this means user is modifying
         
        update = True
        for event_qn_index in range(len(event_questions)):
            event_qn = event_questions[event_qn_index]
            event_qn_ord_choices = event_qn.choice_set.all().order_by('pk')
            num_choices = len(event_qn_ord_choices)
            if num_choices > 0 : # Retrieve user's response for that choice
                choiceresponse_formset[choiceresponse_index].fields['response_value'].queryset = event_qn_ord_choices
                all_formsets.append((event_qn, None, choiceresponse_formset[choiceresponse_index]))
                choiceresponse_qns.append(event_qn)
                choiceresponse_choices.append(event_qn_ord_choices)
                choiceresponse_index += 1
            else : # Retrieve user's response for that question
                all_formsets.append((event_qn, openresponse_formset[openresponse_index], None))
                openresponse_index += 1
                openresponse_qns.append(event_qn)
    else: # User is answering afresh, need to generate new form with right number of OpenResponse and ChoiceResponse objects
        needs_openresponse_forms = []
        num_openresponse_qns = 0
        num_choiceresponse_qns = 0
        for event_qn_index in range(len(event_questions)):
            event_qn = event_questions[event_qn_index]
            num_choices = len(event_qn.choice_set.all())
            print("Number of choices for qn %s :"%event_qn.qn_text)
            print(str(num_choices))
            if num_choices > 0 : # Choice question, create choice response forms
                needs_openresponse_forms.append(False)
                choiceresponse_qns.append(event_qn)
                choiceresponse_choices.append(event_qn.choice_set.all().order_by('pk'))
                choiceresponse_index += 1
                num_choiceresponse_qns += 1
            else : # Open question, just append a single open response form
                #choiceresponse_formsets.append(None)
                needs_openresponse_forms.append(True)
                openresponse_qns.append(event_qn)
                num_openresponse_qns += 1
        print(num_openresponse_qns)
        openresponse_formset_creator.extra = num_openresponse_qns
        openresponse_formset = openresponse_formset_creator(queryset = OpenResponse.objects.none(), prefix = 'open')
        choiceresponse_formset_creator.extra = num_choiceresponse_qns
        choiceresponse_formset = choiceresponse_formset_creator(queryset = ChoiceResponse.objects.none(), prefix = 'choice')
        print("Length of open response formset:" + str(len(openresponse_formset)))
        print("Length of choice response formset:" + str(len(choiceresponse_formset)))
        openresponses_added = 0
        choiceresponses_added = 0
        for index in range(len(needs_openresponse_forms)) :            
            if needs_openresponse_forms[index] :
                all_formsets.append((openresponse_qns[openresponses_added],openresponse_formset[openresponses_added], None))
                openresponses_added += 1
            else:
                choiceresponse_form = choiceresponse_formset[choiceresponses_added]
                print("Trying to limit queryset to : " + str(choiceresponse_choices[choiceresponses_added]))
                choiceresponse_form.fields['response_value'].queryset = choiceresponse_choices[choiceresponses_added] # Limit to only relevant choice objects
                print("Queryset after trying to limit it: " + str(choiceresponse_form.fields['response_value'].queryset))
                all_formsets.append((choiceresponse_qns[choiceresponses_added], None, choiceresponse_form))
                choiceresponses_added += 1
    open_formset_management = openresponse_formset.management_form
    choice_formset_management = choiceresponse_formset.management_form
    print("Choice response questions: " + str(choiceresponse_qns))
    print("Open response questions: " + str(openresponse_qns))
    [print("Choices for choiceqn: " + str(choices)) for choices in choiceresponse_choices]

    # Apply filter of finalized questions
    #event_unfinalized_questions = event_questions.filter(finalized=False).order_by('pk')
    #event_finalized_questions = event_questions.filter(finalized=True).order_by('pk')
    usable_formsets = []
    finalized_qns = []
    usable_open_qns = []
    usable_choice_qns = []
    for qn_index in range(len(all_formsets)) :
        if all_formsets[qn_index][0].finalized :
            finalized_qns.append(all_formsets[qn_index])
        else :
            usable_formsets.append(all_formsets[qn_index])
            if all_formsets[qn_index][1] == None:
                usable_choice_qns.append(all_formsets[qn_index][0])
            else:
                usable_open_qns.append(all_formsets[qn_index][0])
    all_formsets = usable_formsets
    print("Usable formsets: " + str(usable_formsets))
    print("finalized formsets: " + str(finalized_qns))

    active_open_set = current_user_openresponses.filter(qn_for__finalized=False).order_by('pk')
    active_choice_set = current_user_choiceresponses.filter(qn_for__finalized=False).order_by('pk')

    openresponse_formset_creator.extra = len(usable_open_qns) - len(active_open_set)
    openresponse_formset = openresponse_formset_creator(queryset = active_open_set, prefix = 'open')

    choiceresponse_formset_creator.extra = len(usable_choice_qns) - len(active_choice_set)
    choiceresponse_formset = choiceresponse_formset_creator(queryset = active_choice_set, prefix = 'choice')

    open_formset_management = openresponse_formset.management_form
    choice_formset_management = choiceresponse_formset.management_form
    '''
    openresponse_formset_creator = modelformset_factory(OpenResponse, fields = ('response_value',), extra=0)
    openresponse_formset = openresponse_formset_creator(queryset = current_user_openresponses, prefix = 'open')
    choiceresponse_formset_creator = modelformset_factory(ChoiceResponse, fields= ('response_value',), extra=0)
    choiceresponse_formset = choiceresponse_formset_creator(queryset = current_user_choiceresponses, prefix = 'choice')

    '''
    if request.method == 'POST' :
        # Validate open responses
        #submitted_open_responses = openresponse_formset_creator(request.POST, initial=current_user_openresponses, prefix='open')
        print("POST BODY: " + str(request.POST))
        submitted_open_responses = openresponse_formset_creator(request.POST, initial=active_open_set, prefix='open') 
        print("Length of submitted open responses: " + str(len(submitted_open_responses)))
        if submitted_open_responses.is_valid() :
            print("Open responses are valid!")
            if update :
                new_open_responses = submitted_open_responses.save() # done with open responses, since their qn_for and user_from are already in db
                print("Saved all modifications to open responses")
                # now for choice responses
                #for choice_question_index in range(len(choiceresponse_formsets)):

                #submitted_choice_responses = choiceresponse_formset_creator(request.POST, initial=current_user_choiceresponses, prefix='choice')
                submitted_choice_responses = choiceresponse_formset_creator(request.POST, initial=active_choice_set, prefix='choice')

                for submitted_choice_response_index in range(len(submitted_choice_responses)):
                    submitted_choice_response_form = submitted_choice_responses[submitted_choice_response_index]
                    #submitted_choice_response_form.fields['response_value'].queryset = choiceresponse_choices[submitted_choice_response_index]
                    submitted_choice_response_form.fields['response_value'].queryset = usable_choice_qns[submitted_choice_response_index].choice_set.all().order_by('pk')
                    print("Current length of queryset for validating form of choice responses: " + str(len(submitted_choice_response_form.fields['response_value'].queryset))) 
                
                if submitted_choice_responses.is_valid() :
                    print("Choice responses are valid!")
                    new_choice_responses = submitted_choice_responses.save()
                    print("Saved all modifications to choice responses")
                    return redirect(user_home, username=request.user.username)
                print("Errors in choice responses")
                [print(submitted_choice_response.errors) for submitted_choice_response in submitted_choice_responses] 
                return redirect(rsvp_event, eventname) 
                
            else: # need to save user_from, qn_for fields as well as choice_for field for choiceresponses              
                #new_open_responses = submitted_open_responses.save(commit=False)
                #for open_response in new_open_responses:
                for open_response_form_index in range(len(submitted_open_responses)) : # need to iterate through to get matching qn index, since returned and original are of different lengths
                    open_response_form = submitted_open_responses[open_response_form_index]
                    new_open_response = open_response_form.save(commit=False)
                    new_open_response.user_from = user
                    #new_open_response.qn_for = openresponse_qns[open_response_form_index]
                    new_open_response.qn_for = usable_open_qns[open_response_form_index]
                    #print("Saving new open response %s"%new_open_response.response_value)
                    new_open_response.save()
                    print("About to commit new open response to db")
                    open_response_form.save_m2m()
                print("Done saving all new open responses")
                # now for choice responses
                #for choice_question_index in range(len(choiceresponse_formsets)):
                #submitted_choice_responses = choiceresponse_formset_creator(request.POST, initial=current_user_choiceresponses, prefix='choice')
                submitted_choice_responses = choiceresponse_formset_creator(request.POST, initial=active_choice_set, prefix='choice')
                if not submitted_choice_responses.is_valid() :
                    print("Errors in choice responses")
                    [print(choice_response_form.errors) for choice_response_form in submitted_choice_responses]
                    return redirect(rsvp_event, eventname)
                for choice_response_form_index in range(len(submitted_choice_responses)) :
                    choice_response_form = submitted_choice_responses[choice_response_form_index]
                    new_choice_response = choice_response_form.save(commit=False)
                    new_choice_response.user_from = user
                    #new_choice_response.qn_for = choiceresponse_qns[choice_response_form_index]
                    new_choice_response.qn_for = usable_choice_qns[choice_response_form_index]
                    new_choice_response.save()
                    print("About to commit new choice response to db")
                    choice_response_form.save_m2m()
                print("Done with new choice responses!")
                return redirect(user_home, username=request.user.username)
                
        else: # open responses invalid
            print("Errors in open responses")
            [print(open_response_form.errors) for open_response_form in submitted_open_responses]
            return redirect(rsvp_event, eventname)
    else:
        #context = {'event_name': event_name, 'event_date': date, 'event_start': start, 'event_end': end, 'formset': all_formsets, 'formset_management': formset_management}
        context = {'event_name': event.eventname, 'event_date': event.date, 'event_start': event.start_time, 'event_end': event.end_time, 'user_name' : user.username,'formset': all_formsets, 'open_formset_management': open_formset_management, 'choice_formset_management': choice_formset_management, 'finalized_qns': finalized_qns}
        return render(request, 'eventSystem/rsvp_event.html', context)

@login_required
def view_event_responses_vendor(request, event): # owner can view all responses, vendors can view only responses marked visible to them
    if not user_vendor_for_event(request, event):
        return HttpResponse(content="Sorry, you are not a vendor for event %s"%event.eventname, status=401, reason="Unauthorized")
    # User is now known to be vendor of event
    # Retrieve set of questions visible to vendor
    user = User.objects.filter(username=request.user.username)[0]
    event = Event.objects.filter(eventname=event)[0]
    visible_qns = user.visible_to.all().filter(event_for=event).order_by('pk')
    qn_data = [] # list of (qn, [(choices, choice_counts),], open_response_list) tuples
    finalize_formset_creator = modelformset_factory(Question, fields=('finalized',), extra = 0)
    finalize_formset = finalize_formset_creator(queryset = visible_qns)
    '''
    modelformset_factory(OpenResponse, fields = ('response_value',), extra=0)
    openresponse_formset = openresponse_formset_creator(queryset = current_user_openresponses, prefix = 'open')
    '''
    for visible_qn_index in range(len(visible_qns)) :
        visible_qn = visible_qns[visible_qn_index]
        qn_choices = visible_qn.choice_set.all().order_by('pk')
        qn_open_response_list = visible_qn.openresponse_set.all().order_by('pk')
        qn_choice_counts = [len(choice.choices.all()) for choice in qn_choices]
        qn_choice_tuples = [(qn_choices[index], qn_choice_counts[index]) for index in range(len(qn_choices))]
        #qn_data.append((visible_qn, (qn_choices, qn_choice_counts), qn_open_response_list))
        qn_data.append((visible_qn, qn_choice_tuples, qn_open_response_list, finalize_formset[visible_qn_index]))   
    print("Info tuple : " + str(qn_data))
          
    if request.method == "POST":
        finalized_formset = finalize_formset_creator(request.POST, initial=visible_qns)
        if finalized_formset.is_valid() :
            print("Finalization changed")
            modified_qns = finalized_formset.save()
            return redirect(user_home, username=user.username)
        print("Errors finalizing: ")
        [print(finalize_form.errors) for finalize_form in finalized_formset]
        # Error message
        return redirect(view_event_responses_vendor, event=event)

    else:
        context = {'qn_data': qn_data, 'event_name' : event.eventname, 'event_date' : event.date, 'event_start' : event.start_time, 'event_end': event.end_time, 'user_name' : user.username, 'finalize_formset' : finalize_formset}
        return render(request, 'eventSystem/view_event_responses_vendor.html', context=context)
    
@login_required
def view_event_responses_owner(request, event):
    if not user_owns_event(request, event):
        return HttpResponse(content="Sorry, you are not the owner of event %s"%event.eventname, status=401, reason="Unauthorized")
    return HttpResponse(content="Coming Soon!", status=200)
    
    
@login_required    
def add_qn_new_event(request):
    if not hasattr(request, 'user') or not hasattr(request.user, 'username'):
        print("Rejecting request from unknown user")
        return HttpResponse(content="You are not a registered and logged-in user", status=401, reason="Unauthorized")
                                    
    if request.method != "POST":
        return HttpResponse(content="This URL is for POST requests only.", status=200)

    user = User.objects.filter(username=request.user.username)[0]
    user_ordered_events = user.owners.all().order_by('pk')
    if len(user_ordered_events) == 0:
        print("User has not created any events yet.")
        return HttpResponse(content="No event found for this user", status = 404, reason = "You have no events")
    user_latest_event = user_ordered_events[len(user_ordered_events) - 1] # query sets don't allow the -1 indexing for some reason        
    print("Event name : %s"%user_latest_event.eventname)

    # validate qns, save with commit=false
    #errors = []
    valid_qns = []
    qn_choices = []
    print("Post body: " + str(request.body))
    body_unicode = request.body.decode('utf-8')
    body = json.loads(body_unicode)
    print("Parsed body: " + str(body))
    #print("Post data: " + str(request.POST))
    #for new_qn_json in request.POST:
    for new_qn_json in body:
        new_qn_form = QuestionForm(new_qn_json)
        if new_qn_form.is_valid() :
            new_qn = new_qn_form.save(commit=False)
            # set event of qns to this event     
            new_qn.event_for = user_latest_event
            valid_qns.append(new_qn)
            # include choices
            new_qn_choices = new_qn_json["Choices"]
            qn_choices.append(new_qn_choices)
        else:
            return HttpResponse(content="Invalid question detected. Not saving. Cause for rejection: %s"%new_qn_form.errors, status=200)
    # Save to DB
    if len(valid_qns) > 0:
        for valid_qn_index in range(len(valid_qns)):
            valid_qn = valid_qns[valid_qn_index]
            valid_qn.save() 
            print("Saved question %s"%valid_qn.qn_text)
            valid_qn_choices = qn_choices[valid_qn_index]
            if len(valid_qn_choices) > 0:
                print("Multiple Choice question detected. Saving choices")
                for choice in valid_qn_choices :
                    new_choice_form = ChoiceForm({'choice_text':choice})
                    if not new_choice_form.is_valid() :
                        print("Not saving choice")
                    else:
                        new_choice = new_choice_form.save(commit=False)
                        new_choice.qn_for = valid_qn
                        new_choice.save()
                        print("saved qn, now saving foreign key")
                        new_choice_form.save_m2m()
                        print("Saved foreign key!")
            else:
                print("Open Response question detected")
            
    user_home_url = "/eventSystem/users/%s"%request.user
    print("Saved all questions, about to redirect user to his home page %s"%user_home_url)
    return JsonResponse({'redirect_to':user_home_url})
    

# Helper function used by event_home and modify_event
def user_owns_event(request, eventname):
    eventSet = Event.objects.filter(eventname = eventname)
    if len(eventSet) == 0:
        raise Http404("Event does not exist")
    event = eventSet[0]
    user = User.objects.filter(username=request.user.username)[0]
    return event in user.owners.all()
    '''
    event_owners = event.getOwners()
    event_owners_names = [owner.username for owner in event_owners]
    print("Owners: " + str(event_owners_names))
    return request.user.username in event_owners_names # If user is not owner of this event, cannot view its homepage, only other pages like guest view or vendor view of event
    '''

def user_vendor_for_event(request, eventname):
    eventSet = Event.objects.filter(eventname = eventname)
    if len(eventSet) == 0:
        raise Http404("Event does not exist")
    event = eventSet[0]
    user = User.objects.filter(username=request.user.username)[0]
    return event in user.vendors.all()
    '''
    event_vendors = event.getVendors()
    event_vendors_names = [vendor.username for vendor in event_vendors]
    print("Vendors: " + str(event_vendors_names))
    return request.user.username in event_vendors_names
    '''

def user_guest_for_event(request, eventname):
    eventSet = Event.objects.filter(eventname = eventname)
    if len(eventSet) == 0:
        raise Http404("Event does not exist")
    event = eventSet[0]
    user = User.objects.filter(username=request.user.username)[0]
    return event in user.guests.all()
