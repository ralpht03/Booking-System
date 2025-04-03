from flask import Blueprint, render_template, request, flash, redirect, url_for

from website.models import Barber, Client, User
from . import run_query
from flask_login import login_user, login_required, logout_user, current_user
import re

auth = Blueprint('auth', __name__)


@auth.route('/login', methods=['GET', 'POST'])
def login():
  if request.method == 'POST':
    email = request.form.get('email')
    password = request.form.get('password')
    
    user_data = run_query('SELECT * FROM "user" WHERE email = %s', (email,), is_fetch=True)
    user = User.from_dict(user_data)
    
    if user:
      if user.password == password:
        login_user(user, remember=True)
        if user.is_barber():
          if Barber.get(current_user.id).poor_haircut_notif:
            flash('You recieved a poor review! Do better, be better!', category='error')
            query = '''
              UPDATE public."barber" SET poor_haircut_notif = FALSE WHERE id = %s;
            '''
            run_query(query, (current_user.id,), is_fetch=False)
        else:
          query = '''
            SELECT EXISTS (
                SELECT 1
                FROM appointment
                WHERE client_id = %s
                  AND reviewed = false
                  AND appointment_date = (
                    SELECT MAX(appointment_date)
                    FROM appointment
                    WHERE client_id = %s
                      AND appointment_date >= CURRENT_DATE - INTERVAL '7 days'
                      AND appointment_date <= CURRENT_DATE
                  )
                  AND reviewed = false
            ) AS had_appointment_last_week;
          '''
          review_notif_data = run_query(query, (current_user.id, current_user.id,), is_fetch=True)
          print(review_notif_data[0])
          if review_notif_data[0]['had_appointment_last_week']:
            update_query = '''
              UPDATE public.client SET review_notif = %s WHERE id = %s;
            '''
            run_query(update_query, (review_notif_data[0]['had_appointment_last_week'], current_user.id,), is_fetch=False)
            
          if Client.get(current_user.id).haircut_notif:
            flash('Don\'t forget to schedule a haircut!', category='success')
            
          if Client.get(current_user.id).review_notif:
            return redirect(url_for('views.review'))
          
        flash('Logged in successfully!', category='success')
        return redirect(url_for('views.home'))
      else:
        flash('Incorrect password, try again.', category='error')
    else:
      flash('Email does not exist.', category='error')
  return render_template("login.html", user=current_user)


@auth.route('/logout')
@login_required
def logout():
  logout_user()
  return redirect(url_for('auth.login'))


@auth.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
  if request.method == 'POST':
    fname = request.form.get('fname')
    lname = request.form.get('lname')
    email = request.form.get('email')   
    password1 = request.form.get('password1')
    password2 = request.form.get('password2')

    if password1 != password2:
      flash('Passwords don\'t match.', category='error')
    elif len(password1) < 8:
      flash('Password must be at least 8 characters.', category='error')
    elif len(password1) > 12:
      flash('Password must be at most 12 characters.', category='error')
    elif not re.search("[A-Z]", password1):
      flash('Password must contain at least one capital letter.',
            category='error')
    elif not re.search("\d", password1):
      flash('Password must contain at least one digit.', category='error')
    elif not re.search("[^A-Za-z0-9]", password1):
      flash('Password must contain at least one special character.',
            category='error')
    elif User.from_dict(run_query('SELECT * FROM "user" WHERE email = %s', (email,), is_fetch=True)):
      flash('Email already exists.', category='error')
    else:
      query = '''
        INSERT INTO public.client (email, password, first_name, last_name, haircut_notif, review_notif)
        VALUES (%s, %s, %s, %s, DEFAULT, DEFAULT) RETURNING id, email, password, first_name, last_name;
      '''
      
      user_data = run_query(query, (email, password1, fname, lname,), is_fetch=True)
      user = User.from_dict(user_data)
      
      if user:
        flash('Account created!', category='success')
        login_user(user, remember=True)
      else:
        flash('User data is not available or invalid.', category='error')

      return redirect(url_for('views.home'))

  return render_template("sign_up.html", user=current_user)