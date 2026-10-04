"""
Directly sets a known password for any existing account — no interactive
prompts, no copy-pasting long random strings. Use this whenever a login
isn't working and you want to be 100% sure what the password is.

Usage (run from the project root, with the backend venv active):
    python scripts/set_password.py admin@safevoice.app MyNewPassword123

If the account doesn't exist yet, this tells you clearly instead of failing silently.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app import create_app
from app.extensions import db
from app.models.user import User


def main():
    if len(sys.argv) != 3:
        print("Usage: python scripts/set_password.py <email> <new_password>")
        sys.exit(1)

    email, password = sys.argv[1].strip().lower(), sys.argv[2]
    if len(password) < 8:
        print("Password must be at least 8 characters.")
        sys.exit(1)

    app = create_app("development")
    with app.app_context():
        user = User.query.filter_by(email=email).first()
        if not user:
            print(f"No account found with email: {email}")
            print("Check the exact spelling, or run scripts/seed_database.py first.")
            sys.exit(1)

        user.set_password(password)
        user.is_active = True
        db.session.commit()
        print(f"Done. {email} (role: {user.role}) now has the password you just typed.")
        print("Log in at the matching portal: /login (user), /therapist/login, or /admin/login.")


if __name__ == "__main__":
    main()
