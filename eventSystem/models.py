from django.db import models
from django import forms
from django.forms import ModelForm
from django.forms.widgets import CheckboxSelectMultiple, Select

from django.utils import timezone
import datetime

# Create your models here.
class User(models.Model):
    username = models.CharField(max_length = 50, unique = True, blank = False, error_messages={'required': 'Please provide a unique username'})
    email = models.EmailField(max_length = 100, unique = True, blank = False, error_messages={'required': 'Please provide your email address.'}) # Validation doesn't quite seem to work yet

    def __str__(self):
        return self.username
    
    def isOwnerOf(self):
        return Event.objects.has_owner(self)
    
    def isVendorOf(self):
        return Event.objects.has_vendor(self)
    
    def isGuestOf(self):
        return Event.objects.has_guest(self)
    
    def createEvent(self, eventName, dateTime):
        newEvent = Event.objects.create_event(eventName, dateTime)
        newEvent.save()
        newEvent.addOwner(self)
    
class EventManager(models.Manager):
    def create_event(self, eventName, dateTime):
        event = self.create(eventname = eventName, date_time = dateTime)
        return event
    # TO-DO : Can rewrite in terms of SQL queries instead of .all() for optimization
    def has_owner(self, user):
        return [e for e in self.all() if user in e.owners.all()]

    def has_vendor(self, user):
        return [e for e in self.all() if user in e.vendors.all()]

    def has_guest(self, user):
        return [e for e in self.all() if user in e.guests.all()]
           
class Event(models.Model):
    eventname = models.CharField(max_length = 100) 
    date = models.DateField(default = timezone.now, blank = False)
    start_time = models.TimeField(default = timezone.now, blank = False)
    end_time = models.TimeField(default = timezone.now, blank = False)
    owners = models.ManyToManyField(User, related_name="owners")
    vendors = models.ManyToManyField(User, related_name="vendors")
    guests = models.ManyToManyField(User, related_name="guests")
    plus_ones = models.BooleanField(default = False)

    objects = EventManager()

    def __str__(self):
        return self.eventname

    def addOwner(self, user):
        self.owners.add(user)

    def addVendor(self, user):
        self.vendors.add(user)

    def addGuest(self, user):
        self.guests.add(user)

    def getOwners(self):
        return self.owners.all()

    def getVendors(self):
        return self.vendors.all()

    def getGuests(self):
        return self.guests.all()

    def get_questions(self):
        return self.question_set.all()

    # Can be called to figure out who to email if new questions are added
    def get_all_responders(self):
        return [responder for responder in question.get_responders() for question in self.get_questions()]

    def get_all_responder_emails(self): # Called when new questions are added to the event
        return [user.email for user in self.get_all_responders()]
    
    def addUsers(self, newUsers): # newUsers is a dict of {'new_owners':[...], 'new_vendors':[...], 'new_guests':[...]}
        [self.addOwner(new_owner) for new_owner in newUsers['new_owners']]
        [self.addVendor(new_vendor) for new_vendor in newUsers['new_vendors']]
        [self.addGuest(new_guest) for new_guest in newUsers['new_guests']]

    # Have a safe_modify_event method which allows modification of event name after checking eventname doesn't clash with other event of same user?
        
class Question(models.Model):
    qn_text = models.CharField(max_length = 200)
    event_for = models.ForeignKey(Event, on_delete = models.CASCADE)
    finalized = models.BooleanField(default = False)
    
    def __str__(self):
        return self.qn_text
    
    def get_responses(self):
        return self.response_set.all()

    def get_responders(self): # Temp, only tracks if a user responded to this question... does not know if user's choice is affected by modifying options to qn
        return [response.user_from for response in self.get_responses()]

    def get_responder_emails(self): # Called when an extra option is added to the question (only relevant to SingleChoiceQuestion and MCQ?)
        return [responder.email for responder in self.get_responders()]
    
    def get_vendors_set(self):
        return {'username__in' : list(map(lambda x : x.username, self.event_for.getVendors()))}

    visible_to = models.ManyToManyField(User, related_name="visible_to")

    def set_visible_to(self, vendors): # rewrites the entire visible_to set, implicitly ignores any passed in vendor who is not registered as a vendor of the event
        current_visible_to = self.visible_to.all()
        event_vendors = self.get_vendors_set()
        for vendor in event_vendors:
            if vendor in vendors and vendor not in current_visible_to:
                self.visible_to.add(vendor)
            elif vendor not in vendors and vendor in current_visible_to:
                self.visible_to.remove(vendor)

    def finalize(self):
        self.finalized = True
                
    def safe_modify_text(self, text):
        sibling_choices = Choice.objects.filter(qn_for=self.qn_for)
        sibling_choices_texts = [choice.choice_text for choice in sibling_choices]
        if text not in sibling_choices_texts:
            self.choice_text = text
            self.save()
            return True
        return False

class Choice(models.Model): # For creation of question and tracking of response
    choice_text = models.CharField(max_length = 100, unique = False)
    #qn_for = models.ForeignKey(ChoiceQuestion, on_delete = models.CASCADE, primary_key = False)
    qn_for = models.ForeignKey(Question, on_delete = models.CASCADE, primary_key = False)
    # Is there a clear handle on a choice object from the front-end?

    def __str__(self):
        return self.choice_text
    
    def getChoosers(self): # helper for below func
        return self.choiceresponse_set.all()

    def getChooserEmails(self): # use this to retrieve responses and therefore users who must be emailed when this choice gets deleted  
        return [response.user_from.email for response in getChoosers()]

    def safe_modify_text(self, text): # can check that text does not clash with that of other choices for same qn
        sibling_choices = Choice.objects.filter(qn_for=self.qn_for)
        sibling_choices_texts = [choice.choice_text for choice in sibling_choices]
        if text not in sibling_choices_texts:
            self.choice_text = text
            self.save()
            return True
        return False
    
class Response(models.Model):
    qn_for = models.ForeignKey(Question, on_delete = models.CASCADE)
    user_from = models.ForeignKey(User, on_delete = models.CASCADE)
    for_plus_one = models.BooleanField(default = False)

    class Meta: # Tables will only exist for OpenResponse and ChoiceResponse
        abstract = True

class OpenResponse(Response):
    response_value = models.CharField(max_length = 200, blank = False, default="", error_messages={'required': 'Please answer the question'})
    def __str__(self):
        return self.response_value
    
class ChoiceResponse(Response):
    response_value = models.ManyToManyField(Choice, related_name='choices') # Use ManyToManyField instead of ForeignKey to allow multiple choices?
    #choice_for = models.ForeignKey(Choice, on_delete = models.CASCADE)
    def __str__(self):
        return self.response_value
    
# Form Classes
class MyModelMultipleChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        return obj.username
        
class EventForm(ModelForm):
    eventname = models.CharField(max_length = 100, help_text = "Please choose a unique name for your event")
    #date_time = models.DateTimeField(help_text = "When should the event take place")
    date = models.DateField(help_text = "When should the event take place?")
    #start_time = models.TimeField(help_text = "Start Time", input_formats = ['%I:%M %p'])
    start_time = forms.fields.TimeField(input_formats = ['%I:%M %p', '%H:%M:%S', '%H:%M'])
    #end_time = models.TimeField(help_text = "End Time", input_formats = ['%I:%M %p'])
    
    end_time = forms.fields.TimeField(input_formats = ['%I:%M %p', '%H:%M:%S', '%H:%M'])
    owners = MyModelMultipleChoiceField(queryset = User.objects.all(), widget = CheckboxSelectMultiple(), required = False)
    vendors = MyModelMultipleChoiceField(queryset = User.objects.all(), widget = CheckboxSelectMultiple(), required = False)
    guests = MyModelMultipleChoiceField(queryset = User.objects.all(), widget = CheckboxSelectMultiple(), required = False)
    plus_ones = forms.BooleanField(help_text = "Plus Ones?", required=False)
    class Meta:
        model = Event
        fields = ['eventname', 'date', 'start_time', 'end_time', 'owners', 'vendors', 'guests', 'plus_ones'] # TO-DO: Add questions... OR, can be done with AJAX later on

class VisibleToVendorField(forms.ModelMultipleChoiceField):
    def __init__(self, *args, **kwargs):
        #super(VisibleToVendorField, self).__init__(*args, **kwargs)
        event = kwargs.pop('event', None)
        super(VisibleToVendorField, self).__init__(*args, **kwargs)
        self.required = False
        if event:
            qn_event_vendor_names = [vendor.username for vendor in event.getVendors()]
            self.queryset = User.objects.filter(username__in = qn_event_vendor_names)
        
class QuestionForm(ModelForm):
    qn_text = models.CharField(max_length = 200)
    visible_to = forms.ModelMultipleChoiceField(queryset = User.objects.all(), widget = CheckboxSelectMultiple(), required = False) 

    class Meta:
        model = Question
        fields = ['qn_text', 'visible_to']

class ChoiceForm(ModelForm):
    choice_text = models.CharField(max_length = 100)
    class Meta:
        model = Choice
        fields = ['choice_text']

class OpenResponseForm(ModelForm):
    response_value = forms.CharField(max_length = 200, help_text = "Please answer the question in under 200 characters")
    class Meta:
        model = OpenResponse
        fields = ['response_value']
        

class ChoiceResponseForm(ModelForm):
    response_value = forms.ModelMultipleChoiceField(queryset = Choice.objects.all(), widget = CheckboxSelectMultiple(), required = True)
    class Meta:
        model = ChoiceResponse
        fields = ['response_value']    

class FinalizeForm(ModelForm):
    finalized = forms.BooleanField(required = False)
    class Meta:
        model = Question
        fields = ['finalized']
'''
class SingleChoiceResponseForm(ModelForm):
    #response_value = forms.ChoiceField(choices = [])
    response_value = forms.NullBooleanField()
    class Meta:
        model = ChoiceResponse
        fields = ['response_value']

class MCQResponseForm(ModelForm):
    #response_value = forms.MultipleChoiceField(choices = [])
    response_value = forms.NullBooleanField()
    class Meta:
        model = ChoiceResponse
        fields = ['response_value']
'''
