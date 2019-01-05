:: Runs the app for development purposes (on Windows).
set FLASK_APP=main.py
set FLASK_ENV=development
set SECRET_KEY=development-only
flask run --host=0.0.0.0