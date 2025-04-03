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
  - python-dotenv for environment variable management

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

3. Environment Configuration:
   - Create a '.env' file in the root directory with the following variables:
     '''
     DB_NAME=your_database_name
     DB_USER=your_database_user
     DB_PASSWORD=your_database_password
     DB_HOST=your_database_host
     DB_PORT=5432
     SECRET_KEY=your_secret_key
     '''
   - Replace the placeholder values with your actual database credentials
   - The application uses these environment variables to connect to your PostgreSQL database

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
  - '__init__.py' - Flask application initialization and database configurations
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
