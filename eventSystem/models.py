from django.db import models
#from django import forms
from django.forms import ModelForm

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
    eventname = models.CharField(max_length = 100, unique = True)
    date_time = models.DateTimeField('when')
    owners = models.ManyToManyField(User, related_name="owners")
    vendors = models.ManyToManyField(User, related_name="vendors")
    guests = models.ManyToManyField(User, related_name="guests")

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

class EventForm(ModelForm):
    eventname = models.CharField(max_length = 100, help_text = "Please choose a unique name for your event")
    date_time = models.DateTimeField(help_text = "When should the event take place")
    class Meta:
        model = Event
        fields = ['eventname', 'date_time'] # TO-DO: Add questions
