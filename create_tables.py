from app import app, db
from app import User, Playlist

with app.app_context():
    db.create_all()

print("Tables created successfully.")
