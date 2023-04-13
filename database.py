# database.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class Experience(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    summary_id = db.Column(
        db.Integer, db.ForeignKey("summary.id"), nullable=True)
    message_type = db.Column(
        db.Enum("system", "assistant", "user"), nullable=False)
    author = db.Column(db.Enum("AI", "user", "environment"), nullable=False)
    ai_id = db.Column(db.String(100), nullable=True)
    ai_name = db.Column(db.String(100), nullable=True)
    thoughts = db.Column(db.Text, nullable=True)
    to_user = db.Column(db.Text, nullable=True)
    user_name = db.Column(db.String(100), nullable=True)
    user_message = db.Column(db.Text, nullable=True)
    commands = db.Column(db.Text, nullable=True)
    date_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class Summary(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    summary = db.Column(db.Text, nullable=False)
    date_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    experiences = db.relationship("Experience", backref="summary", lazy=True)


def get_latest_messages(ai_name, messages_number):
    latest_messages = (
        Experience.query.filter_by(ai_name=ai_name)
        .order_by(Experience.date_time.desc())
        .limit(messages_number)
        .all()
    )
    return latest_messages[::-1]


def save_user_message(user_name, user_message, ai_id, ai_name):
    user_entry = Experience(
        message_type="user",
        author="user",
        ai_id=ai_id,
        ai_name=ai_name,
        user_name=user_name,
        user_message=user_message,
    )
    db.session.add(user_entry)
    db.session.commit()


def save_ai_message(ai_id, ai_name, thoughts, to_user, commands):
    ai_entry = Experience(
        message_type="assistant",
        author="AI",
        ai_id=ai_id,
        ai_name=ai_name,
        thoughts=thoughts,
        to_user=to_user,
        commands=commands,
    )
    db.session.add(ai_entry)
    db.session.commit()


def save_environment_message(ai_id, ai_name, commands):
    environment_entry = Experience(
        message_type="system",
        author="environment",
        ai_id=ai_id,
        ai_name=ai_name,
        commands=commands,
    )
    db.session.add(environment_entry)
    db.session.commit()
