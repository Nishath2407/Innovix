"""
Seeds a fresh database so every part of SafeVoice has something real to use:
  * one admin account
  * 10 verified therapist accounts (with weekly availability) so booking works immediately
  * mental-health / safety resources

Run from the project root:   python scripts/seed_database.py
Start over from scratch:     python scripts/seed_database.py --reset

Credentials are printed ONCE at the end. Set ADMIN_EMAIL / ADMIN_PASSWORD /
SEED_PASSWORD in your environment if you'd rather choose them yourself.
"""
import os
import sys
import secrets
from datetime import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app import create_app
from app.extensions import db
from app.models.user import User, UserProfile
from app.models.therapist import Therapist, TherapistSpecialization, TherapistLanguage, TherapistAvailability, TherapistCredential
from app.models.resource import Resource

THERAPISTS = [
    ("Dr. Ananya Rao", "M.Phil Clinical Psychology", 8, 1400, "female", ["anxiety", "workplace_burnout"], ["en", "te"], ["video", "audio", "text"],
     "Focuses on workplace stress and anxiety using CBT-informed approaches.", "evening"),
    ("Dr. Sana Kapoor", "M.A. Counseling Psychology", 5, 1100, "female", ["relationships", "self_confidence"], ["en", "hi"], ["audio", "text"],
     "Works with young professionals navigating relationship and confidence challenges.", "day"),
    ("Dr. Meera Iyer", "Ph.D. Clinical Psychology", 11, 1800, "female", ["grief", "trauma"], ["en"], ["video", "text"],
     "Trauma-informed therapist with a decade of experience in grief counseling.", "day"),
    ("Rohan Verma", "M.A. Psychology, RCI Licensed", 6, 1200, "male", ["stress", "workplace_burnout"], ["en", "hi"], ["video", "audio", "text"],
     "Helps working professionals manage burnout and rebuild sustainable routines.", "evening"),
    ("Dr. Priya Nair", "M.D. Psychiatry", 14, 2200, "female", ["anxiety", "trauma"], ["en", "hi"], ["video", "audio"],
     "Psychiatrist with a focus on anxiety disorders and trauma recovery.", "day"),
    ("Arjun Menon", "M.A. Counseling", 4, 900, "male", ["self_confidence", "general_wellbeing"], ["en"], ["text", "audio"],
     "Works with college students on confidence, motivation and adjustment.", "evening"),
    ("Dr. Kavya Reddy", "M.Phil Clinical Psychology", 9, 1500, "female", ["womens_safety", "workplace_harassment"], ["en", "te"], ["video", "audio", "text"],
     "Supports women through workplace harassment and safety concerns.", "day"),
    ("Dr. Farah Sheikh", "Ph.D. Psychology", 12, 1900, "female", ["trauma", "womens_safety"], ["en", "hi"], ["video", "audio", "text"],
     "Trauma specialist supporting survivors of domestic violence and abuse.", "evening"),
    ("Vikram Singh", "M.A. Counseling Psychology", 7, 1300, "male", ["stress", "relationships"], ["en", "hi"], ["video", "audio", "text"],
     "Integrative approach to stress management and relationship counseling.", "day"),
    ("Dr. Lakshmi Menon", "M.D. Psychiatry", 16, 2400, "female", ["general_wellbeing", "anxiety"], ["en", "te", "hi"], ["video", "audio", "text"],
     "Senior psychiatrist offering holistic mental wellbeing support.", "evening"),
]

WINDOWS = {  # IST wall-clock windows per weekday
    "day": [(time(9), time(13)), (time(14), time(18))],
    "evening": [(time(11), time(14)), (time(17), time(21))],
}

RESOURCES = [
    ("Understanding workplace burnout", "stress",
     "Burnout builds gradually. Early signs include exhaustion, growing cynicism about work, and reduced effectiveness. Rest alone rarely fixes it — talking to someone, setting boundaries and reviewing workload usually matters more.",
     "https://www.who.int/news/item/28-05-2019-burn-out-an-occupational-phenomenon-international-classification-of-diseases"),
    ("A 5-minute grounding exercise for anxiety", "anxiety",
     "Name 5 things you can see, 4 you can touch, 3 you can hear, 2 you can smell and 1 you can taste. Breathe out slowly between each step. Grounding won't remove anxiety, but it can bring you back to the present.", None),
    ("When stress starts affecting your sleep", "stress",
     "Keep a fixed wake-up time, avoid screens for the last 30 minutes before bed, and write tomorrow's worries down before sleeping. If poor sleep lasts more than a few weeks, speak to a professional.", None),
    ("What to do after workplace harassment", "workplace_harassment",
     "Write down what happened, when, and who witnessed it, and keep any messages. In India, employers with 10 or more employees must have an Internal Committee under the POSH Act, 2013 that you can complain to. You can also seek legal advice or support from a counsellor before deciding what to do.", None),
    ("Digital safety basics", "digital_safety",
     "Turn on two-factor authentication, review which apps can see your location, and check for unknown devices signed into your accounts. If you're worried someone is monitoring your phone, use a device they've never touched.", None),
    ("Digital safety: reporting cybercrime", "digital_safety",
     "Online harassment, stalking, and financial fraud can be reported through the National Cyber Crime Reporting Portal (cybercrime.gov.in) or by calling 1930 for financial fraud. Verify numbers on the official portal before relying on them.", "https://cybercrime.gov.in"),
    ("Planning ahead if home isn't safe", "domestic_violence",
     "A safety plan lists people you trust, places you can go, and important documents and items to keep within reach. You can build a private one in My Safety Plan. Only you can see it.", None),
    ("Women's helpline (India)", "domestic_violence",
     "The national Women Helpline number is 181 and is meant for women affected by violence. Availability can vary by state — verify locally, and call emergency services if you're in immediate danger.", None),
    ("Emergency numbers (India)", "emergency",
     "For immediate danger, call 112, India's unified emergency number. SafeVoice is not an emergency service and can't send help to your location.", None),
    ("Tele-MANAS: free mental-health support (India)", "emergency",
     "Tele-MANAS is a government tele-mental-health service. The number is 14416, and it's listed on the official Tele-MANAS site. Verify the number on the official site before relying on it.", "https://telemanas.mohfw.gov.in"),
    ("How to support a friend who is struggling", "mental_health",
     "Listen without rushing to fix. Ask directly how they are, avoid comparing their pain to others', and gently suggest professional support. Offer to help them find a therapist or sit with them while they book.", None),
    ("Rebuilding self-confidence, one small step at a time", "self_confidence",
     "Set one small goal each day, and write down one thing you handled well. Confidence usually follows evidence, not the other way around.", None),
]


def run(reset=False):
    app = create_app("development")
    with app.app_context():
        if reset:
            db.drop_all()
            print("Dropped existing tables.")
        db.create_all()

        admin_email = os.environ.get("ADMIN_EMAIL", "admin@safevoice.app").lower()
        admin_pw = os.environ.get("ADMIN_PASSWORD")
        shared_pw = os.environ.get("SEED_PASSWORD")
        created_admin = created_therapists = False

        if not User.query.filter_by(email=admin_email).first():
            admin_pw = admin_pw or "Admin-" + secrets.token_urlsafe(9) + "7"
            u = User(email=admin_email, role="admin", is_email_verified=True)
            u.set_password(admin_pw)
            db.session.add(u)
            db.session.flush()
            db.session.add(UserProfile(user_id=u.id, display_name="SafeVoice Admin"))
            created_admin = True

        if Therapist.query.count() == 0:
            shared_pw = shared_pw or "Sv-" + secrets.token_urlsafe(9) + "7"
            for name, qual, yrs, price, gender, specs, langs, modes, bio, shift in THERAPISTS:
                slug = name.lower().replace("dr. ", "").replace(" ", ".")
                u = User(email=f"{slug}@safevoice.app", role="therapist", is_email_verified=True)
                u.set_password(shared_pw)
                db.session.add(u)
                db.session.flush()
                db.session.add(UserProfile(user_id=u.id, display_name=name))
                t = Therapist(user_id=u.id, display_name=name, qualification=qual, bio=bio, years_experience=yrs,
                              gender=gender, session_price=price, session_modes_json=modes, is_verified=True,
                              verification_status="approved")
                db.session.add(t)
                db.session.flush()
                db.session.add_all(TherapistSpecialization(therapist_id=t.id, name=s) for s in specs)
                db.session.add_all(TherapistLanguage(therapist_id=t.id, language=l) for l in langs)
                db.session.add(TherapistCredential(therapist_id=t.id, credential_type="Registration (sample data)",
                                                   details="Seeded account", verification_status="approved"))
                for weekday in range(7 if shift == "evening" else 6):  # day-shift therapists take Sundays off
                    for start, end in WINDOWS[shift]:
                        db.session.add(TherapistAvailability(therapist_id=t.id, weekday=weekday, start_time=start, end_time=end))
            created_therapists = True

        if Resource.query.count() == 0:
            for title, cat, body, url in RESOURCES:
                db.session.add(Resource(title=title, category=cat, body=body, source_url=url))

        db.session.commit()

        print("\n=== SafeVoice seed complete ===")
        if created_admin:
            print(f"Admin login      ->  {admin_email}  /  {admin_pw}     (portal: /admin/login)")
        else:
            print(f"Admin {admin_email} already exists (password unchanged).")
        if created_therapists:
            print(f"Sample therapists ->  e.g. ananya.rao@safevoice.app  /  {shared_pw}   (portal: /therapist/login)")
            print("                      (all 10 sample therapists share that password; emails are firstname.lastname@safevoice.app)")
        else:
            print("Therapist accounts already exist (passwords unchanged).")
        print("Create a client account yourself from /register.\n")


if __name__ == "__main__":
    run(reset="--reset" in sys.argv)
