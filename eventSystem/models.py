from django.db import models
from django import forms
from django.forms import ModelForm
from django.forms.widgets import CheckboxSelectMultiple, Select

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
    date_time = models.DateTimeField('when')
    owners = models.ManyToManyField(User, related_name="owners")
    vendors = models.ManyToManyField(User, related_name="vendors")
    guests = models.ManyToManyField(User, related_name="guests")
    plus_one = models.BooleanField(default = False)

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

    def get_responses(self):
        return self.response_set.all()

    def get_responders(self): # Temp, only tracks if a user responded to this question... does not know if user's choice is affected by modifying options to qn
        return [response.user_from for response in self.get_responses()]

    def get_responder_emails(self): # Called when an extra option is added to the question (only relevant to SingleChoiceQuestion and MCQ?)
        return [responder.email for responder in self.get_responders()]
    
    def get_vendors_set(self):
        return {'username__in' : list(map(lambda x : x.username, self.event_for.getVendors()))}

    visible_to = models.ManyToManyField(User, related_name="visble_to", limit_choices_to = get_vendors_set) # Tracks which vendors can see the responses to the question

    def safe_modify_text(self, text):
        sibling_choices = Choice.objects.filter(qn_for=self.qn_for)
        sibling_choices_texts = [choice.choice_text for choice in sibling_choices]
        if text not in sibling_choices_texts:
            self.choice_text = text
            self.save()
            return True
        return False

    '''
class ChoiceQuestion(Question): # Also needs to keep track of which response has been chosen by which user
    #next_id = 0 # monotonically increasing counter
 
    def getRespondersForChoice(self, choice_id):
        # filter response_set by choice_id to retrieve responses which are going to be deleted, then email users linked to those responses
        return self.choiceresponse_set.filter(choice_id = choice_id)
    def gen_choice_id(self): # should be called before saving each ChoiceResponse to DB
        next_id += 1
        return next_id
    def save_choice_response(self, choice_response): # call this function instead of choice_response.save()
        choice_response.choice_id = gen_choice_id() 
        choice_response.choice_id.save()
    '''

class Choice(models.Model): # For creation of question and tracking of response
    choice_text = models.CharField(max_length = 100, unique = False)
    #qn_for = models.ForeignKey(ChoiceQuestion, on_delete = models.CASCADE, primary_key = False)
    qn_for = models.ForeignKey(Question, on_delete = models.CASCADE, primary_key = False)
    # Is there a clear handle on a choice object from the front-end?
    
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
    #qn_for = models.ForeignKey(Question, on_delete = models.CASCADE)
    response_value = models.CharField(max_length = 200, blank = False, default="", error_messages={'required': 'Please answer the question'})
    
class ChoiceResponse(Response):
    #qn_for = models.ForeignKey(ChoiceQuestion, on_delete = models.CASCADE)
    response_value = models.NullBooleanField() # More flexible than BooleanField?
    #choice_id = models.PositiveSmallIntegerField() # Used to track who should be notified when a given response is deleted
    #choice_for = models.OneToOneField(Choice, on_delete = models.CASCADE, default = None, primary_key = False)
    choice_for = models.ForeignKey(Choice, on_delete = models.CASCADE)
    
# Form Classes
class MyModelMultipleChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        return obj.username
        
class EventForm(ModelForm):
    eventname = models.CharField(max_length = 100, help_text = "Please choose a unique name for your event")
    date_time = models.DateTimeField(help_text = "When should the event take place")
    owners = MyModelMultipleChoiceField(queryset = User.objects.all(), widget = CheckboxSelectMultiple())
    vendors = MyModelMultipleChoiceField(queryset = User.objects.all(), widget = CheckboxSelectMultiple())
    guests = MyModelMultipleChoiceField(queryset = User.objects.all(), widget = CheckboxSelectMultiple())
    plus_one = forms.BooleanField(help_text = "Plus Ones?")
    class Meta:
        model = Event
        fields = ['eventname', 'date_time', 'owners', 'vendors', 'guests', 'plus_one'] # TO-DO: Add questions... OR, can be done with AJAX later on

class QuestionForm(ModelForm):
    qn_text = models.CharField(max_length = 200)
    visible_to = forms.ModelMultipleChoiceField(queryset = User.objects.all(), widget = CheckboxSelectMultiple()) # how to ensure only vendors get listed here in queryset?
    class Meta:
        model = Question
        fields = ['qn_text', 'visible_to']

        '''
class ChoiceQuestionForm(QuestionForm):
    choice_text = models.CharField(max_length = 100)
    class Meta:
        model = ChoiceQuestion
        '''
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
    response_value = forms.NullBooleanField()
    class Meta:
        model = ChoiceResponse
        fields = ['response_value']    
        
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
