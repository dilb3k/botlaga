from datetime import datetime
from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    chat_id: Mapped[int] = mapped_column(ForeignKey("chats.id", onupdate="CASCADE"), index=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"))
    source_session_id: Mapped[int | None] = mapped_column(ForeignKey("quiz_sessions.id"))
    status: Mapped[str] = mapped_column(String(16), default="active")
    interval: Mapped[int] = mapped_column(Integer)
    duration: Mapped[int] = mapped_column(Integer)
    total: Mapped[int | None] = mapped_column(Integer)
    sent: Mapped[int] = mapped_column(Integer, default=0)
    queue: Mapped[list] = mapped_column(JSONB, default=list)
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    lease_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    lease_token: Mapped[str | None] = mapped_column(String(36))
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    __table_args__ = (
        Index(
            "one_live_session_per_chat",
            "chat_id",
            unique=True,
            postgresql_where=text("status IN ('active','paused','stopping')"),
        ),
        Index("session_due", "status", "next_run_at"),
        CheckConstraint("status IN ('active','paused','stopping','finished','blocked')"),
        CheckConstraint("interval BETWEEN 60 AND 86400"),
        CheckConstraint("duration BETWEEN 5 AND 2628000"),
        CheckConstraint("total IS NULL OR total > 0"),
    )


class SessionQuestion(Base):
    __tablename__ = "session_questions"
    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("quiz_sessions.id"), index=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"))
    poll_id: Mapped[str | None] = mapped_column(String(128), unique=True)
    chat_id: Mapped[int] = mapped_column(ForeignKey("chats.id", onupdate="CASCADE"))
    message_id: Mapped[int | None] = mapped_column(BigInteger)
    snapshot: Mapped[dict] = mapped_column(JSONB)
    correct: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(16), default="sending")
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    closes_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    aggregate: Mapped[dict] = mapped_column(JSONB, default=dict)
    poll_update_id: Mapped[int] = mapped_column(BigInteger, default=-1)
    __table_args__ = (
        Index(
            "one_open_question",
            "session_id",
            unique=True,
            postgresql_where=text("status IN ('sending','open')"),
        ),
        CheckConstraint("status IN ('sending','open','closed','uncertain','failed')"),
    )


class Answer(Base):
    __tablename__ = "answers"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    session_question_id: Mapped[int] = mapped_column(ForeignKey("session_questions.id"), index=True)
    option: Mapped[int | None] = mapped_column(Integer)
    correct: Mapped[bool] = mapped_column(Boolean)
    points: Mapped[int] = mapped_column(Integer)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    elapsed_ms: Mapped[int] = mapped_column(BigInteger)
    update_id: Mapped[int] = mapped_column(BigInteger)
    __table_args__ = (
        UniqueConstraint("user_id", "session_question_id"),
        CheckConstraint("points IN (0,1)"),
        CheckConstraint("elapsed_ms >= 0"),
    )


class FSMRecord(Base):
    __tablename__ = "fsm_records"
    key: Mapped[str] = mapped_column(String(200), primary_key=True)
    state: Mapped[str | None] = mapped_column(String(200))
    data: Mapped[dict] = mapped_column(JSONB, default=dict)
