# Event RSVP System | Django Web-App
### ECE 590 | Spring 2017

## About
The `Event RSVP System` is a web application based on the [*Django*](https://www.djangoproject.com/) framework. 
This application allows users to create events and provides an interface to manage the event's owners, vendors, and guests.
Moreover, this application provides an intuitive system for managing guest questionnaires and vendor permissions.

## Usage
### Prerequisites
* Django
* Postgresql
* Python3

### Creating the Database
Through your preferred method, create a postgresql database titled
`eventSystem`. 

### Configuring Django
Clone this repository and navigate to the root directory. Use `python3` to make any migrations, and then apply
those migrations.
```
$ python3 manage.py makemigrations
$ python3 manage.py migrate
```

### Starting the Development Server
To start the server for development, run the following command:
```
python3 manage.py runserver 0.0.0.0:8000
```
This will cause the web app to listen on all public IPs on port `8000`. If you wish to only run the 
web app locally, use:
```
python3 manage.py runserver
```
The default port will still be `8000`.

### Accessing the application
This step may vary depending on your environment. If the server is running on your local machine
navigate to:
```
http://127.0.0.1:8000/eventSystem/login/
```
Otherwise, navigate to the IP of your remote server:
```
http://[ YOUR SERVER'S IP/ADDRESS ]:8000/eventSystem/login/
```
### Setting up Email
Open `settings.py` under `events/`. Find the section titled `Email Settings` and fill our your email credentials.
