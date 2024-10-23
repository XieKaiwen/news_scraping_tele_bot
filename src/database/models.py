from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
import uuid
from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    tele_id = Column(String, unique=True, nullable=False)  # tele_user_id
    name = Column(String, nullable=False)  # tele_username


class TopicPreference(Base):
    __tablename__ = "topicsPreferences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    topic_name = Column(String, nullable=False)
    topic_hash = Column(String, nullable=False)
    country_code = Column(String, nullable=False, default="US")
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)


class UserQuery(Base):
    __tablename__ = "userQueries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    query = Column(String, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
