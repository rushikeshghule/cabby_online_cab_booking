# Cabby - Role-Based Cab Booking App

A full-stack Django application for cab booking with role-based access control.

## Features

### Rider Features
- Sign up / login as a rider
- Book rides with pickup and drop locations
- View available drivers nearby
- Live ride status updates
- Chat with assigned driver
- Rate driver after ride completion
- View ride history

### Driver Features
- Sign up / login as a driver
- Document verification system
- Accept/reject ride requests
- Real-time location updates
- Start/end rides
- View earnings
- Chat with riders

### Admin Features
- Admin dashboard
- Monitor all rides and active drivers
- Track earnings
- Driver approval system
- User management

## Tech Stack
- Backend: Django + Django REST Framework
- Frontend: Django Templates with Bootstrap
- Real-time Features: Django Channels + WebSockets
- Database: PostgreSQL
- Maps Integration: Google Maps API
- Authentication: Django built-in auth

## Setup Instructions

1. Clone the repository
```bash
git clone https://github.com/yourusername/cabby.git
cd cabby
```

2. Create and activate virtual environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Set up environment variables
Create a `.env` file in the project root and add:
```
SECRET_KEY=your_secret_key
DEBUG=True
GOOGLE_MAPS_API_KEY=your_google_maps_api_key
```

5. Run migrations
```bash
python manage.py migrate
```

6. Create superuser
```bash
python manage.py createsuperuser
```

7. Run the development server (Django WSGI)
```bash
python manage.py runserver
```

Or, to run with Daphne (ASGI, required for WebSockets and production):
```bash
daphne -b 0.0.0.0 -p 8001 cabby.asgi:application
```

- Use `runserver` for local development and quick testing.
- Use `daphne` for production or when you need WebSocket support (real-time features).

Visit http://localhost:8000 (for runserver) or http://localhost:8001 (for Daphne) to access the application.

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License
[MIT](https://choosealicense.com/licenses/mit/) 