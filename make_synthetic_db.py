# Makes synthetic.db, a small fake database to test the server against.
# The names are made up, there is no real data in here.
# run once:  python make_synthetic_db.py

from sqlalchemy import create_engine, text

engine = create_engine("sqlite:///synthetic.db")

with engine.begin() as conn:
    conn.execute(text("DROP TABLE IF EXISTS comms_metadata"))
    conn.execute(text("DROP TABLE IF EXISTS people"))

    conn.execute(text("""
        CREATE TABLE people (
            id INTEGER PRIMARY KEY,
            name TEXT,
            role TEXT,
            dept TEXT
        )
    """))

    conn.execute(text("""
        CREATE TABLE comms_metadata (
            id INTEGER PRIMARY KEY,
            sender_id INTEGER,
            recipient_id INTEGER,
            timestamp TEXT,
            subject_length INTEGER
        )
    """))

    people = [
        {"id": 1, "name": "Fake Alice", "role": "VP Engineering", "dept": "Engineering"},
        {"id": 2, "name": "Fake Bob", "role": "Senior Analyst", "dept": "Finance"},
        {"id": 3, "name": "Fake Carla", "role": "Ops Manager", "dept": "Operations"},
        {"id": 4, "name": "Fake Dave", "role": "IT Admin", "dept": "IT"},
        {"id": 5, "name": "Fake Elena", "role": "CFO", "dept": "Finance"},
    ]

    for p in people:
        conn.execute(text(
            "INSERT INTO people (id, name, role, dept) VALUES (:id, :name, :role, :dept)"
        ), p)

    # only metadata here, who messaged who and when. no message content.
    messages = [
        {"id": 1, "sender_id": 4, "recipient_id": 1, "timestamp": "2026-01-05T09:00:00", "subject_length": 40},
        {"id": 2, "sender_id": 4, "recipient_id": 2, "timestamp": "2026-01-06T10:15:00", "subject_length": 22},
        {"id": 3, "sender_id": 4, "recipient_id": 3, "timestamp": "2026-01-06T14:30:00", "subject_length": 18},
        {"id": 4, "sender_id": 1, "recipient_id": 4, "timestamp": "2026-01-07T08:05:00", "subject_length": 55},
        {"id": 5, "sender_id": 5, "recipient_id": 2, "timestamp": "2026-01-08T11:45:00", "subject_length": 30},
    ]

    for m in messages:
        conn.execute(text(
            "INSERT INTO comms_metadata (id, sender_id, recipient_id, timestamp, subject_length) "
            "VALUES (:id, :sender_id, :recipient_id, :timestamp, :subject_length)"
        ), m)

print("synthetic.db created: 5 people, 5 messages")
