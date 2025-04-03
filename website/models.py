from datetime import datetime, time
from json import JSONEncoder
import json
import time
from typing import Optional

from flask_login import UserMixin, current_user

from website import run_query

######################################################################
#                             USER                                   #
######################################################################
class User(UserMixin):
    def __init__(self, id, email, password, first_name, last_name):
        self.id = id
        self.email = email
        self.password = password
        self.first_name = first_name
        self.last_name = last_name

    @staticmethod
    def get(user_id):
        if user_id is None or not str(user_id).isdigit():
            return None
        query = '''
        SELECT id, email, password, first_name, last_name
        FROM public."user" 
        WHERE id = %s;
        '''
        user_data = run_query(query, (user_id,), is_fetch=True)
        if user_data:
            # Ensure that user_data is unpacked properly
            user_info = user_data[0] if user_data else None
            if user_info:
                return User(
                    id=user_info['id'],
                    email=user_info['email'],
                    password=user_info['password'],
                    first_name=user_info['first_name'],
                    last_name=user_info['last_name']
                )
        return None
    
    @staticmethod
    def is_barber():
        query = '''
            SELECT u.id, (b.id IS NOT NULL AND c.id IS NULL) AS is_barber
            FROM public."user" u
            LEFT JOIN public.barber b ON u.id = b.id
            LEFT JOIN public.client c ON u.id = c.id
            WHERE u.id = %s;
        '''
        barber_id = run_query(query, (current_user.id,), is_fetch=True)
        return barber_id[0]['is_barber']
    
    @staticmethod
    def from_dict(data):
        # Handle the case where data might be a list containing a dictionary or RealDictRow
        if isinstance(data, list) and len(data) > 0:
            data = data[0]

        # Check if the data behaves like a dictionary
        if isinstance(data, dict):
            return User(
                id=data.get('id'),
                email=data.get('email', ''),  # Provide default empty string if key is missing
                password=data.get('password', ''),
                first_name=data.get('first_name', ''),
                last_name=data.get('last_name', '')
            )
        else:
            return None  # Return None or raise an exception if data format is incorrect



######################################################################
#                           BARBER                                   #
######################################################################
class Barber(User):
    def __init__(self, id, email, password, first_name, last_name, poor_haircut_notif):
        super().__init__(id, email, password, first_name, last_name)
        self.poor_haircut_notif = poor_haircut_notif
        
    @staticmethod
    def get(barber_id):
        if barber_id is None or not str(barber_id).isdigit():
            return None
        query = '''
        SELECT *
        FROM public."barber" 
        WHERE id = %s;
        '''
        barber_data = run_query(query, (barber_id,), is_fetch=True)
        if barber_data:
            # Ensure that user_data is unpacked properly
            barber_info = barber_data[0] if barber_data else None
            if barber_info:
                return Barber(
                    id=barber_info['id'],
                    email=barber_info['email'],
                    password=barber_info['password'],
                    first_name=barber_info['first_name'],
                    last_name=barber_info['last_name'],
                    poor_haircut_notif=barber_info['poor_haircut_notif']
                )
        return None

    @staticmethod
    def from_dict(data):
        # Handle the case where data might be a list containing a dictionary or RealDictRow
        if isinstance(data, list) and len(data) > 0:
            data = data[0]

        # Check if the data behaves like a dictionary and has all necessary keys
        if isinstance(data, dict):
            return Barber(
                id=data.get('id'),
                email=data.get('email', ''),
                password=data.get('password', ''),
                first_name=data.get('first_name', ''),
                last_name=data.get('last_name', ''),
                poor_haircut_notif=data.get('poor_haircut_notif', False)  # Default to False if not provided
            )
        else:
            return None  # Return None or raise an exception if data format is incorrect



######################################################################
#                           Client                                   #
######################################################################
class Client(User):
    def __init__(self, id, email, password, first_name, last_name, haircut_notif, review_notif):
        super().__init__(id, email, password, first_name, last_name)
        self.review_notif = review_notif
        self.haircut_notif = haircut_notif
        
    @staticmethod
    def get(client_id):
        if client_id is None or not str(client_id).isdigit():
            return None
        query = '''
        SELECT *
        FROM public."client" 
        WHERE id = %s;
        '''
        client_data = run_query(query, (client_id,), is_fetch=True)
        if client_data:
            # Ensure that user_data is unpacked properly
            client_info = client_data[0] if client_data else None
            if client_info:
                return Client(
                    id=client_info['id'],
                    email=client_info['email'],
                    password=client_info['password'],
                    first_name=client_info['first_name'],
                    last_name=client_info['last_name'],
                    review_notif=client_info['review_notif'],
                    haircut_notif=client_info['haircut_notif']
                )
        return None

    @staticmethod
    def from_dict(data):
        # Handle the case where data might be a list containing a dictionary or RealDictRow
        if isinstance(data, list) and len(data) > 0:
            data = data[0]

        # Check if the data behaves like a dictionary and has all necessary keys
        if isinstance(data, dict):
            return Client(
                id=data.get('id'),
                email=data.get('email', ''),
                password=data.get('password', ''),
                first_name=data.get('first_name', ''),
                last_name=data.get('last_name', ''),
                review_notif=data.get('review_notif', False),
                haircut_notif=data.get('haircut_notif', False)
            )
        else:
            return None  # Return None or raise an exception if data format is incorrect



######################################################################
#                          SERVICE                                   #
######################################################################
class Service:
    def __init__(self, id: Optional[int], name: str, price: float, barber_id: int):
        self.service_id = id
        self.name = name
        self.price = price
        self.barber_id = barber_id

    @staticmethod
    def from_dict(data):
        return Service(
            id=data.get('id'),
            name=data['name'],
            price=data['price'],
            barber_id=data['barber_id']
        )



######################################################################
#                         SCHEDULE                                   #
######################################################################
class Schedule:
    def __init__(self, id: Optional[int], barber_id: Optional[int], work_date: str, start_time: str, end_time: str):
        self.id = id
        self.barber_id = barber_id
        self.work_date = work_date
        self.start_time = start_time
        self.end_time = end_time

    @staticmethod
    def from_dict(data):
        return Schedule(
            id=data.get('id'),
            barber_id=data['barber_id'],
            work_date=data['work_date'],
            start_time=data['start_time'],
            end_time=data['end_time']
        )
        
    @staticmethod
    def get_formatted_schedule(data):
        formatted_data = []
        for entry in data:
            # Extract values
            id = entry['id']
            work_date = entry['work_date']
            start_time = entry['start_time']
            end_time = entry['end_time']
            barber_id = entry['barber_id']

            # Format entry with checks against the directly imported types
            formatted_entry = {
                'id': id,
                'work_date': work_date.strftime('%a, %d %b %Y'),
                'start_time': start_time.strftime('%H:%M'),
                'end_time': end_time.strftime('%H:%M'),
                'barber_id': barber_id
            }
            formatted_data.append(formatted_entry)
        return formatted_data



######################################################################
#                           REVIEW                                   #
######################################################################
class Review:
    def __init__(self, id, barber_id, client_id, rating, note):
        self.id = id
        self.barber_id = barber_id
        self.client_id = client_id
        self.rating = rating
        self.note = note

    @staticmethod
    def from_dict(data):
        # Handle the case where data might be a list containing a dictionary or RealDictRow
        if isinstance(data, list) and len(data) > 0:
            data = data[0]

        # Check if the data behaves like a dictionary and has all necessary keys
        if isinstance(data, dict):
            return Review(
                id=data.get('id'),
                barber_id=data.get('barber_id'),
                client_id=data.get('client_id'),
                rating=data.get('rating'),
                note=data.get('note')
            )
        else:
            return None  # Return None or raise an exception if data format is incorrect



######################################################################
#                         CUSTOM ENCODER                             #
######################################################################
class CustomEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, time):
            return obj.strftime('%H:%M:%S')
        elif isinstance(obj, datetime):
            return obj.isoformat()
        return json.JSONEncoder.default(self, obj)