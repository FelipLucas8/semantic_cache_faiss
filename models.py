from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
import uuid

db = SQLAlchemy()


class VectorMapping(db.Model):
    __tablename__ = 'VectorMappings'

    id = db.Column(db.Integer, primary_key=True)
    # If NULL = global cache scope
    user_id = db.Column(db.Integer, nullable=True)
    prompt_language = db.Column(
        db.String(50), nullable=False, default='Português')
    embedding = db.Column(db.LargeBinary, nullable=False)
    scope = db.Column(db.String, nullable=False)
    content = db.Column(db.String, nullable=False)
    usage_count = db.Column(db.Integer, default=0)
    created_at = db.Column(
        db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow,
                           onupdate=datetime.utcnow)


class User(db.Model):
    __tablename__ = 'User'
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    role = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    isNew = db.Column(db.Boolean, nullable=False, default=True)
    prompt_language = db.Column(
        db.String(50), nullable=False, default='Português')
    ui_language = db.Column(
        db.String(50), nullable=False, default='pt'
    )
    release_notes_check = db.Column(db.Boolean, nullable=False, default=False)
    view_release = db.Column(db.Boolean, nullable=True, default=True)
