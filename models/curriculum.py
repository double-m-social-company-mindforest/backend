from sqlalchemy import Column, Integer, String, TIMESTAMP, ForeignKey, text, CheckConstraint, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship
from database.connection import Base


class UserCurriculumSession(Base):
    __tablename__ = "user_curriculum_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    session_number = Column(Integer, nullable=False, index=True)
    session_data = Column(JSON, nullable=False)
    status = Column(String(20), nullable=False, default="not_started", index=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'))
    updated_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'))
    completed_at = Column(TIMESTAMP(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", backref="curriculum_sessions")

    # Constraints
    __table_args__ = (
        UniqueConstraint('user_id', 'session_number', name='uq_user_session'),
        CheckConstraint('session_number >= 1 AND session_number <= 8', name='check_session_number'),
    )