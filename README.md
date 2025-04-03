# Barbershop Booking System

A full-featured web application for managing barbershop appointments, services, and customer reviews. This system allows customers to book appointments with barbers, manage their profiles, and leave reviews. Barbers can manage their schedules, services, and view customer feedback.

## Features

- **User Authentication**
  - Separate user roles for clients and barbers
  - Secure login and registration

- **Client Features**
  - Browse available barbers
  - Book appointments
  - View and manage upcoming appointments
  - Leave reviews for barbers
  - Receive notifications for upcoming haircuts

- **Barber Features**
  - Manage personal schedule and availability
  - Add and manage services with pricing
  - View customer feedback
  - Notification preferences for poor rating alerts

- **Administrative Functions**
  - User management
  - Service management
  - Appointment oversight

## Tech Stack

- **Backend**
  - Python
  - Flask web framework
  - Flask-Login for authentication
  - PostgreSQL database

- **Frontend**
  - HTML, CSS, JavaScript
  - Jinja2 templates
  - Bootstrap for responsive design

## Database Schema

The application uses a PostgreSQL database with tables for:
- Users (with client and barber subtypes)
- Services
- Schedules
- Appointments
- Reviews

## Setup and Installation

### Prerequisites
- Python 3.x
- PostgreSQL database

### Installation Steps

1. Clone the repository:
   '''
   git clone https://github.com/ralpht03/booking-system.git
   cd booking-system
   '''

2. Install the required dependencies:
   '''
   pip install -r requirements.txt
   '''

3. Database Configuration:
   - The application is configured to connect to a PostgreSQL database
   - Update the database connection details in 'website/__init__.py'

## Running the Application

For Windows:
'''
python main.py
'''

For Mac/Linux:
'''
python3 main.py
'''

The application will be accessible at `http://127.0.0.1:5000/` in your web browser.

## Project Structure

- 'main.py' - Application entry point
- 'website/' - Main application package
  - '__init__.py' - Flask application initialization
  - 'models.py' - Database models
  - 'auth.py' - Authentication routes
  - 'views.py' - Main application routes
  - 'templates/' - HTML templates
  - 'static/' - Static files (CSS, JavaScript, images)

## Usage

1. Register as either a barber or a client
2. Log in to access your respective dashboard
3. Clients can book appointments and leave reviews
4. Barbers can manage their schedule and services
