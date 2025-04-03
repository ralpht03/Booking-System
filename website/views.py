from os import abort
from flask import Blueprint, jsonify, redirect, render_template, request, url_for
from flask_login import login_required, current_user
from website import run_query
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import current_user, login_required

from website.models import Client, Review, Schedule, Service
from . import run_query

views = Blueprint('views', __name__)



######################################################################
#                             BASE                                   #
######################################################################
@views.route('/', methods=['GET', 'POST'])
def home():
    return render_template("home.html", user=current_user)



######################################################################
#                         SERVICES                                   #
######################################################################
@login_required
@views.route('/view-services', methods=['GET', 'POST'])
def view_service():
    if current_user.is_barber():
        query = "SELECT unnest(enum_range(NULL::services)) as name;"
        services_data = run_query(query, is_fetch=True)
        services = [service['name'] for service in services_data]
        return render_template("service.html", user=current_user, services=services)
    else:
        return redirect(url_for('views.home'))


@login_required
@views.route('/services', methods=['GET', 'POST'])
def services():
    if current_user.is_barber():
        if request.method == 'GET':
            query = "SELECT * FROM \"service\" where \"barber_id\" = %s"
            try:
                services = run_query(query, (current_user.id,))
                return jsonify(services)
            except Exception as e:
                print(e)
                abort(500, description=str(e))

        elif request.method == 'POST':
            data = request.json
            
            # Check if the new service name already exists excluding the current service
            check_query = "SELECT COUNT(*) FROM \"service\" WHERE \"name\" = %s AND \"barber_id\" = %s"
            existing_count = run_query(check_query, (data['name'], current_user.id), is_fetch=True)
            if existing_count[0]['count'] > 0:
                flash('Service name already exists. Please choose a different name.', 'error')
                return jsonify({"error": "Service name already exists. Please choose a different name."}), 400

            service = Service.from_dict(data)
            query = "INSERT INTO \"service\" (\"name\", \"price\", \"barber_id\") VALUES (%s, %s, %s)"
            try:
                run_query(query, (service.name, service.price, service.barber_id), is_fetch=False)
                flash('Service created successfully.', 'success')
                return jsonify({"message": "Service created successfully."})
            except Exception as e:
                print(e)
                abort(500, description=str(e))
    else:
       return redirect(url_for('views.home'))


@login_required
@views.route("/services/<int:id>", methods=['GET', 'PUT', 'DELETE'])
def get_service(id):
  if current_user.is_barber:
    if request.method == 'GET':
        query = "SELECT * FROM \"service\" WHERE \"id\" = %s"
        try:
            service_data = run_query(query, (id,))
            if service_data:
                return jsonify(service_data)
            else:
                abort(404, description="Service not found")
        except Exception as e:
            print(e)
            abort(500, description=str(e))

    elif request.method == 'PUT':
        data = request.json
        
        # Check if the new service name already exists excluding the current service
        check_query = '''SELECT COUNT(*) FROM "service" WHERE name = %s AND barber_id = %s AND id != %s'''
        existing_count = run_query(check_query, (data['name'], current_user.id, id), is_fetch=True)
        if existing_count[0]['count'] > 0:
            flash('Service name already exists. Please choose a different name.', 'error')
            return jsonify({"error": "Service name already exists. Please choose a different name."}), 400

        service = Service.from_dict(data)
        query = "UPDATE \"service\" SET \"name\" = %s, \"price\" = %s WHERE \"id\" = %s"
        try:
            run_query(query, (service.name, service.price, id), is_fetch=False)
            flash('Service updated successfully.', 'success')
            return jsonify({"message": "Service updated successfully."})
        except Exception as e:
            print(e)
            abort(500, description=str(e))
    elif request.method == 'DELETE':
        query = "DELETE FROM \"service\" WHERE \"id\" = %s"
        try:
            run_query(query, (id,), is_fetch=False)
            return jsonify({"message": "Service deleted successfully."})
        except Exception as e:
            print(e)
            abort(500, description=str(e))
    else:
        return redirect(url_for('views.home'))



######################################################################
#                        SCHEDULE                                    #
######################################################################
@login_required
@views.route('/view-schedule', methods=['GET', 'POST'])
def post_schedule():
    if current_user.is_barber():
        return render_template("schedule.html", user=current_user)
    else:
        return redirect(url_for('views.home'))

def populate_time_slots(barber_id, work_date, start_time, end_time):
    # convert times from strings to datetime objects if not already
    if isinstance(work_date, str):
        work_date = datetime.strptime(work_date, '%Y-%m-%d').date()
    if isinstance(start_time, str):
        start_time = datetime.strptime(start_time, '%H:%M').time()
    if isinstance(end_time, str):
        end_time = datetime.strptime(end_time, '%H:%M').time()

    query = """
    INSERT INTO "time_slots" (barber_id, work_date, start_time, end_time, is_available)
    VALUES (%s, %s, %s, %s, TRUE)
    """

    current_time = datetime.combine(work_date, start_time)
    end_time = datetime.combine(work_date, end_time)
    # Generate 30-minute time slots
    while current_time + timedelta(minutes=30) <= end_time:
        slot_end = current_time + timedelta(minutes=30)
        run_query(query, (barber_id, work_date, current_time.time(), slot_end.time()), is_fetch=False)
        # move to the next 30-minute interval
        current_time += timedelta(minutes=30)

def update_schedule(id, new_work_date, new_start_time, new_end_time):
    # fetch data
    if isinstance(new_work_date, str):
        new_work_date = datetime.strptime(new_work_date, '%Y-%m-%d').date()
    if isinstance(new_start_time, str):
        new_start_time = datetime.strptime(new_start_time, '%H:%M').time()
    if isinstance(new_end_time, str):
        new_end_time = datetime.strptime(new_end_time, '%H:%M').time()
        
    # update the schedule in the database
    update_query = """
    UPDATE "schedule" SET work_date = %s, start_time = %s, end_time = %s
    WHERE id = %s;
    """
    try:
        run_query(update_query, (new_work_date, new_start_time, new_end_time, id))
        # now handle time slots
        adjust_time_slots(id, new_work_date, new_start_time, new_end_time)
    except Exception as e:
        print(f"Error updating schedule: {e}")

def adjust_time_slots(schedule_id, work_date, start_time, end_time):
    # delete existing slots that might conflict 
    delete_query = """
    DELETE FROM "time_slots"
    WHERE barber_id = (SELECT barber_id FROM schedule WHERE id = %s) AND work_date = %s;
    """
    run_query(delete_query, (schedule_id, work_date))

    # populate new time slots
    populate_time_slots(schedule_id, work_date, start_time, end_time)

def delete_time_slots(barber_id, work_date):
    query = "DELETE FROM \"time_slots\" WHERE barber_id = %s AND work_date = %s"
    run_query(query, (barber_id, work_date), is_fetch=False)
                          
@login_required
@views.route("/schedule", methods=['GET', 'POST'])
def schedule():
    if current_user.is_barber():
        if request.method == 'GET':
            query = "SELECT * FROM \"schedule\" WHERE barber_id = %s AND work_date >= CURRENT_DATE AND work_date < CURRENT_DATE + INTERVAL '14 days' ORDER BY work_date ASC, start_time ASC"
            try:
                schedule_data = run_query(query, (current_user.id,), is_fetch=True)
                formatted_data = Schedule.get_formatted_schedule(schedule_data)
                return jsonify(formatted_data)
            except Exception as e:
                print(f"Error processing schedule data: {str(e)}")
                abort(500, description=str(e))

        elif request.method == 'POST':
            data = request.json
            
            # Check if the work date is in the past
            work_date = datetime.strptime(data['work_date'], '%Y-%m-%d').date()  # Assuming 'work_date' is passed as 'YYYY-MM-DD'
            today = datetime.now().date()
            if work_date < today:
                flash('Cannot set schedule for past dates.', 'error')
                return jsonify({"error": "Cannot set schedule for past dates."}), 400

            # Check if start time is before end time            
            start_time = datetime.strptime(data['start_time'], '%H:%M').time()
            end_time = datetime.strptime(data['end_time'], '%H:%M').time()
            if start_time >= end_time:
                flash('Start time must be before end time.', 'error')
                return jsonify({"error": "Start time must be before end time."}), 400
            
            # Check if a schedule already exists for this date and barber
            check_query = "SELECT COUNT(*) FROM \"schedule\" WHERE barber_id = %s AND work_date = %s"
            existing_count = run_query(check_query, (current_user.id, data['work_date']), is_fetch=True)
            if existing_count[0]['count'] > 0:
                flash('Schedule already exists for this date.', 'error')
                return jsonify({"error": "Schedule already exists for this date."}), 400
            
            schedule = Schedule.from_dict(data)
            insert_query = "INSERT INTO \"schedule\" (\"work_date\", \"start_time\", \"end_time\", \"barber_id\") VALUES (%s, %s, %s, %s)"
            try:
                populate_time_slots(schedule.barber_id, schedule.work_date, schedule.start_time, schedule.end_time)
                run_query(insert_query, (schedule.work_date, schedule.start_time, schedule.end_time, schedule.barber_id), is_fetch=False)
                flash('Schedule created successfully.', 'success')
                return jsonify({"message": "Schedule created successfully."})
            except Exception as e:
                print(e)
                abort(500, description=str(e))
    else:
        return redirect(url_for('views.home'))


@login_required
@views.route("schedule/<int:id>", methods=['GET', 'PUT', 'DELETE'])
def manage_schedule(id):
    if current_user.is_barber():
        if request.method == 'GET':
            query = "SELECT * FROM \"schedule\" WHERE \"id\" = %s"
            try:
                schedule_data = run_query(query, (id,))
                for entry in schedule_data:
                    entry['work_date'] = entry['work_date'].strftime('%a, %d %b %Y')
                    if isinstance(entry['start_time'], datetime.time):
                        entry['start_time'] = entry['start_time'].strftime('%H:%M')
                    if isinstance(entry['end_time'], datetime.time):
                        entry['end_time'] = entry['end_time'].strftime('%H:%M')
                if schedule_data:
                    return jsonify(schedule_data)
                else:
                    abort(404, description="Schedule not found")
            except Exception as e:
                print(e)
                abort(500, description=str(e))

        elif request.method == 'PUT':
            data = request.json

            # Check if the work date is in the past
            work_date = datetime.strptime(data['work_date'], '%Y-%m-%d').date()  # Assuming 'work_date' is passed as 'YYYY-MM-DD'
            today = datetime.now().date()
            if work_date < today:
                return jsonify({"error": "Cannot set schedule for past dates."}), 400

            # Check if a schedule already exists for this date and barber
            start_time = datetime.strptime(data['start_time'], '%H:%M').time()
            end_time = datetime.strptime(data['end_time'], '%H:%M').time()
            if start_time >= end_time:
                return jsonify({"error": "Start time must be before end time."}), 400
            
            # Check if there's an existing schedule for the same day with a different ID
            check_query = "SELECT COUNT(*) FROM \"schedule\" WHERE \"barber_id\" = %s AND \"work_date\" = %s AND \"id\" != %s"
            existing_count = run_query(check_query, (current_user.id, data['work_date'], id), is_fetch=True)
            if existing_count[0]['count'] > 0:
                return jsonify({"error": "Another schedule exists on the same day."}), 400
            
            schedule = Schedule.from_dict(data)
            query = "UPDATE \"schedule\" SET \"work_date\" = %s, \"start_time\" = %s, \"end_time\" = %s WHERE \"id\" = %s"
            try:
                update_schedule(id, schedule.work_date, schedule.start_time, schedule.end_time)
                run_query(query, (schedule.work_date, schedule.start_time, schedule.end_time, id), is_fetch=False)
                return jsonify({"message": "Schedule updated successfully."})
            except Exception as e:
                print(e)
                abort(500, description=str(e))

        elif request.method == 'DELETE':
            query = "DELETE FROM \"schedule\" WHERE \"id\" = %s"
            work_date_query = "SELECT work_date, barber_id FROM \"schedule\" WHERE id = %s"
            try:
                work_date_data = run_query(work_date_query, (id,), is_fetch=True)
                if work_date_data:
                    work_date = work_date_data[0]['work_date']
                    barber_id = work_date_data[0]['barber_id']
                    delete_time_slots(barber_id, work_date)
                    run_query(query, (id,), is_fetch=False)
                    flash('Schedule deleted successfully.', 'success')
                    return jsonify({"message": "Schedule deleted successfully."})
                else:
                    flash('Schedule not found.', 'error')
                    abort(404, description="Schedule not found")
            except Exception as e:
                print(e)
                abort(500, description=str(e))
    else:
        return redirect(url_for('views.home'))


######################################################################
#                         BOOKING                                    #
######################################################################
# cleanup time slots
def clean_time_slots():
    query = "CALL cleanup_time_slots_procedure()"
    try:
        run_query(query, is_fetch=False)
    except Exception as e:
        print(f"Error cleaning up time slots: {e}")

# route to fetch barbers and services
@views.route('/get-barbers', methods=['GET'])
def get_barbers():
    query = """
        SELECT b.id AS barber_id, b.first_name, b.last_name, s.id AS service_id, s.name, s.price
        FROM \"barber\" b
        JOIN \"service\" s ON b.id = s.barber_id
        ORDER BY b.id, s.id
    """
    try:
        rows = run_query(query)
        if not rows:
            print("no data returned from query")
        barbers = {}
        for row in rows:
            barber_key = f"{row['first_name']} {row['last_name']}"
            if barber_key not in barbers:
                barbers[barber_key] = []
            barbers[barber_key].append({'barber_id': row['barber_id'], 'service_id': row['service_id'], 'service_name': row['name'], 'price': row['price']})
    except Exception as e:
        print(e)
        return jsonify({"error": "An error occurred while fetching barbers."}), 500
    
    return jsonify(barbers)

@views.route('/get-barber-dates/<int:barber_id>', methods=['GET'])
def get_barber_dates(barber_id):
    query = """
    SELECT DISTINCT work_date FROM \"schedule\"
    WHERE barber_id = %s
    ORDER BY work_date
    """
    try:
        dates = run_query(query, (barber_id,), is_fetch=True)
        work_dates = [date['work_date'].isoformat() for date in dates if date['work_date'] >= datetime.now().date()]
    except Exception as e:
        print(e)
        return jsonify({"error": "An error occurred while fetching barber dates."}), 500

    return jsonify(work_dates)

# route to fetch available times using the view
@views.route('/get-available-times', methods=['POST'])
def get_available_times():
    data = request.json
    barber_id = data['barber_id']
    date = datetime.strptime(data['date'], '%Y-%m-%d').date()

    if date < datetime.now().date():
        flash('Cannot book appointments in the past.', 'error')
        return jsonify({"error": "Cannot book appointments in the past."}), 400

    query = """
    SELECT start_time, end_time FROM "time_slots"
    WHERE barber_id = %s AND work_date = %s AND is_available = TRUE AND (work_date || ' ' || start_time)::timestamp >= CURRENT_TIMESTAMP
    ORDER BY start_time;
    """
    try:
        times = run_query(query, (barber_id, date), is_fetch=True)
        available_times = []
        for time_slot in times:
            start_time = datetime.combine(date, time_slot['start_time'])
            end_time = datetime.combine(date, time_slot['end_time'])
            while start_time + timedelta(minutes=30) <= end_time:
                slot_end = start_time + timedelta(minutes=30)
                if start_time > datetime.now():                  
                    available_times.append({
                        'start_time': start_time.strftime('%H:%M'),
                        'end_time': slot_end.strftime('%H:%M')
                    })
                start_time += timedelta(minutes=30)
    except Exception as e:
        print(e)
        return jsonify({"error": "An error occurred while fetching available times."}), 500

    return jsonify(available_times)

@login_required
@views.route('/get-user-appointments', methods=['GET'])
def get_user_appointments():
    client_id = current_user.id 
    query = """
    SELECT 
    a.appointment_date, 
    a.start_time, 
    a.end_time, 
    b.first_name, 
    b.last_name, 
    s.name AS service_name, 
    s.price
FROM 
    "appointment" a
JOIN 
    "barber" b ON a.barber_id = b.id
JOIN 
    "service" s ON a.service_id = s.id
WHERE 
    a.client_id = %s AND 
    a.appointment_date >= CURRENT_DATE
ORDER BY 
    a.appointment_date ASC, 
    a.start_time ASC;
    """
    try:
        appointments = run_query(query, (client_id,), is_fetch=True)
        results = [{
            'date': appt['appointment_date'].isoformat(),
            'start_time': appt['start_time'].strftime('%H:%M'),
            'end_time': appt['end_time'].strftime('%H:%M'),
            'service_name': appt['service_name'],
            'price': appt['price'],
            'barber_name': f"{appt['first_name']} {appt['last_name']}"
        } for appt in appointments]
    except Exception as e:
        print(e)
        return jsonify({"error": "An error occurred while fetching appointments."}), 500

    return jsonify(results)


# booking endpoint
@login_required
@views.route('/booking', methods=['POST', 'GET'])
def booking():
    if not current_user.is_barber():
        if request.method == 'POST':
            data = request.json
            barber_id = data['barber_id']
            service_id = data['service_id']
            date = data['date']
            start_time = datetime.strptime(data['start_time'], '%H:%M').time()
            end_time = (datetime.combine(datetime.strptime(date, '%Y-%m-%d').date(), start_time) + timedelta(minutes=30)).time()
        
            try:
                query_check_slot = """
                SELECT id FROM "time_slots"
                WHERE barber_id = %s AND work_date = %s AND start_time = %s AND end_time = %s AND is_available = TRUE
                """
                query_update_slot = """
                UPDATE "time_slots" SET is_available = FALSE WHERE id = %s
                """
                query_insert_appointment = """
                INSERT INTO "appointment" (client_id, barber_id, service_id, appointment_date, start_time, end_time)
                VALUES (%s, %s, %s, %s, %s, %s)
                """

                # check if the time slot is available
                slot = run_query(query_check_slot, (barber_id, date, start_time, end_time), is_fetch=True)
                if slot:
                    slot_id = slot[0]['id'] 
                    # update the time slot to not available
                    run_query(query_update_slot, (slot_id,), is_fetch=False)
                    # insert the new appointment
                    run_query(query_insert_appointment, (current_user.id, barber_id, service_id, date, start_time, end_time), is_fetch=False)
                    #flash('Appointment booked successfully.', 'success')
                    return jsonify({"success": "Appointment booked successfully."})
                else:
                    #flash('This time slot is already booked. Please choose another time.', 'error')
                    return jsonify({"error": "This time slot is already booked. Please choose another time."}), 400

            except Exception as e:
                print(e)
                return jsonify({"error": "An error occurred while booking your appointment. Please try again."}), 500
                
        return render_template("booking.html", user=current_user)
    else:
        return redirect(url_for('views.home'))



######################################################################
#                         REVIEWS                                    #
######################################################################
@login_required
@views.route('/review', methods=['GET', 'POST'])
def review():
    if not current_user.is_barber():
        if request.method == 'POST':
            data = request.json
            query = '''
            SELECT
                a.client_id,
                a.barber_id
            FROM
                appointment a
            WHERE
                (a.appointment_date < CURRENT_DATE OR
                (a.appointment_date = CURRENT_DATE AND a.end_time < CURRENT_TIME))
                AND a.client_id = %s
            ORDER BY
                a.appointment_date DESC, a.end_time DESC
            LIMIT 1;
            '''
            review_data = run_query(query, (current_user.id,), is_fetch=True)
            review = Review.from_dict(review_data)
            try:
                query = "INSERT INTO review (barber_id, client_id, rating, note) VALUES (%s, %s, %s, %s)"
                run_query(query, (review.barber_id, current_user.id, data['rating'], data['note']), is_fetch=False)
                query = "UPDATE client SET review_notif = FALSE WHERE id = %s"
                run_query(query, (current_user.id,), is_fetch=False)
                flash('Review submitted successfully.', 'success')
                return jsonify({"message": "Review submitted successfully."})
            except Exception as e:
                print(e)
                flash('An error occurred while submitting the review.', 'error')
                return jsonify({"error": "An error occurred while submitting the review."}), 500
        else:
            user = Client.get(current_user.id)
            if user.review_notif:
                return render_template('post_review.html', user=current_user)
            else:
                return redirect(url_for('views.home'))
    else:
        return redirect(url_for('views.home'))
    


@login_required
@views.route('/view-reviews', methods=['GET'])
def view_reviews():
    if current_user.is_barber():
        query = """
                SELECT review.*, 
                    u2.first_name AS client_first_name, 
                    u2.last_name AS client_last_name
                FROM review
                INNER JOIN "user" u1 ON review.barber_id = u1.id
                INNER JOIN "user" u2 ON review.client_id = u2.id
                WHERE review.barber_id = %s
                ORDER BY review.id DESC
                """
        try:
            reviews_data = run_query(query, (current_user.id,))
            return render_template('reviews.html', reviews=reviews_data, user=current_user)
        except Exception as e:
            print(e)
            return jsonify({"error": "An error occurred while fetching the reviews."}), 500
    else:
        return redirect(url_for('views.home'))
    


@views.route('/crew', methods=['GET', 'POST'])
def crew():
    #clean_time_slots()
    # Retrieve data from the barberinfo view
    query = "SELECT * FROM barberinfo"
    barber_info_data = run_query(query)

    # Process the retrieved data
    barbers = {}
    for data in barber_info_data:
        barber_id = data['barber_id']
        if barber_id not in barbers:
            barbers[barber_id] = {
                'id': barber_id,
                'first_name': data['first_name'],
                'last_name': data['last_name'],
                'email': data['email'],
                'avg_rating': data['avg_rating'],
                'schedule': []
            }

        schedule_entry = {
            'work_date': data['work_date'],
            'start_time': data['start_time'],
            'end_time': data['end_time']
        }
        barbers[barber_id]['schedule'].append(schedule_entry)


    return render_template("crew.html", barbers=list(barbers.values()), user=current_user)



######################################################################
#                         APPOINTMENTS                               #
######################################################################
@login_required
@views.route('/appointments', methods=['GET'])
def appointments():
    if current_user.is_barber():
        if request.method == 'GET':
            barber_id = current_user.id 
            query = """
            SELECT a.appointment_date, a.start_time, a.end_time, c.first_name, c.last_name, s.name AS service_name, s.price
            FROM "appointment" a
            JOIN "client" c ON a.client_id = c.id
            JOIN "service" s ON a.service_id = s.id
            WHERE a.barber_id = %s AND a.appointment_date >= CURRENT_DATE
            ORDER BY a.appointment_date ASC, a.start_time ASC
            """
            try:
                appointments = run_query(query, (barber_id,), is_fetch=True)
                results = [{
                    'date': appt['appointment_date'].isoformat(),
                    'start_time': appt['start_time'].strftime('%H:%M'),
                    'end_time': appt['end_time'].strftime('%H:%M'),
                    'service_name': appt['service_name'],
                    'price': appt['price'],
                    'client_name': f"{appt['first_name']} {appt['last_name']}"
                } for appt in appointments]
            except Exception as e:
                print(e)
                return jsonify({"error": "An error occurred while fetching appointments."}), 500

            return jsonify(results)
    else:
        return redirect(url_for('views.home'))
    
@login_required
@views.route('/view-appointments', methods=['GET'])
def view_appointments():
    if current_user.is_barber():
        return render_template('appointments.html', user=current_user)
