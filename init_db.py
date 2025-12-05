from app import app, db
from app.models import User
from werkzeug.security import generate_password_hash

with app.app_context():
    db.create_all()

    # Create a default user
    if not User.query.filter_by(username='admin').first():
        hashed_password = generate_password_hash('password', method='pbkdf2:sha256')
        new_user = User(username='admin', password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
