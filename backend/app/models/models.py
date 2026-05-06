"""
All SQLAlchemy ORM models for SchoolSaaS
Every table has school_id for multi-tenant isolation
"""
import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import (
    Column, String, Boolean, Integer, DateTime, Date,
    ForeignKey, Text, Numeric, ARRAY, JSON, Enum as SAEnum,
    UniqueConstraint, Index
)
from sqlalchemy.dialects.postgresql import UUID, INET, JSONB
from sqlalchemy.orm import relationship
from app.db.session import Base


def _uuid():
    return str(uuid.uuid4())

def _now():
    return datetime.now(timezone.utc)


# ── Schools ──────────────────────────────────────────────────────────────────

class School(Base):
    __tablename__ = "schools"
    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name            = Column(String(255), nullable=False)
    code            = Column(String(20), unique=True, nullable=False)
    address         = Column(Text)
    phone           = Column(String(20))
    email           = Column(String(255))
    logo_url        = Column(Text)
    subscription    = Column(String(50), default="basic")
    is_active       = Column(Boolean, default=True)
    created_at      = Column(DateTime(timezone=True), default=_now)


# ── Users (All roles unified) ────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"
    id                    = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id             = Column(UUID(as_uuid=True), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False)
    full_name             = Column(String(255), nullable=False)
    email                 = Column(String(255), unique=True, nullable=False)
    phone                 = Column(String(20))
    password_hash         = Column(String(255), nullable=False)
    role                  = Column(String(30), nullable=False)   # admin|teacher|student|parent|principal
    is_active             = Column(Boolean, default=True)
    is_email_verified     = Column(Boolean, default=False)
    must_change_password  = Column(Boolean, default=False)
    last_login            = Column(DateTime(timezone=True))
    failed_login_attempts = Column(Integer, default=0)
    locked_until          = Column(DateTime(timezone=True))
    created_at            = Column(DateTime(timezone=True), default=_now)
    updated_at            = Column(DateTime(timezone=True), default=_now, onupdate=_now)

    __table_args__ = (Index("ix_users_school", "school_id"),)


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id     = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    token_hash  = Column(String(255), unique=True, nullable=False)
    family_id   = Column(String(255))   # Token rotation family — if reuse detected, revoke all
    device_info = Column(Text)
    ip_address  = Column(INET)
    expires_at  = Column(DateTime(timezone=True), nullable=False)
    is_revoked  = Column(Boolean, default=False)
    created_at  = Column(DateTime(timezone=True), default=_now)


# ── Academic Structure ───────────────────────────────────────────────────────

class AcademicYear(Base):
    __tablename__ = "academic_years"
    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id   = Column(UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False)
    year_label  = Column(String(20), nullable=False)
    start_date  = Column(Date, nullable=False)
    end_date    = Column(Date, nullable=False)
    is_current  = Column(Boolean, default=False)


class Class(Base):
    __tablename__ = "classes"
    id               = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id        = Column(UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False)
    academic_year_id = Column(UUID(as_uuid=True), ForeignKey("academic_years.id"))
    name             = Column(String(50), nullable=False)
    section          = Column(String(10))
    class_teacher_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    room_number      = Column(String(20))
    max_students     = Column(Integer, default=40)


class Subject(Base):
    __tablename__ = "subjects"
    id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id  = Column(UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False)
    name       = Column(String(100), nullable=False)
    code       = Column(String(20))
    class_id   = Column(UUID(as_uuid=True), ForeignKey("classes.id"))
    teacher_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    max_marks  = Column(Integer, default=100)


# ── Students ─────────────────────────────────────────────────────────────────

class Student(Base):
    __tablename__ = "students"
    id                  = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id             = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    school_id           = Column(UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False)
    admission_number    = Column(String(50), unique=True, nullable=False)
    roll_number         = Column(String(20))
    class_id            = Column(UUID(as_uuid=True), ForeignKey("classes.id"))
    date_of_birth       = Column(Date)
    gender              = Column(String(10))
    blood_group         = Column(String(5))
    address             = Column(Text)
    parent_id           = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    admission_date      = Column(Date, default=lambda: datetime.now().date())
    photo_url           = Column(Text)
    is_active           = Column(Boolean, default=True)
    # Premium
    is_premium          = Column(Boolean, default=False)
    premium_granted_by  = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    premium_granted_at  = Column(DateTime(timezone=True))
    premium_expires_at  = Column(DateTime(timezone=True))
    premium_note        = Column(Text)


# ── Attendance ───────────────────────────────────────────────────────────────

class Attendance(Base):
    __tablename__ = "attendance"
    id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id  = Column(UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False)
    class_id   = Column(UUID(as_uuid=True), ForeignKey("classes.id"))
    date       = Column(Date, nullable=False)
    status     = Column(String(10))  # present|absent|late|holiday
    marked_by  = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    remarks    = Column(Text)
    created_at = Column(DateTime(timezone=True), default=_now)

    __table_args__ = (
        UniqueConstraint("student_id", "date", name="uq_attendance_student_date"),
        Index("ix_attendance_date", "date"),
    )


# ── Exams & Marks ────────────────────────────────────────────────────────────

class Exam(Base):
    __tablename__ = "exams"
    id               = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id        = Column(UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False)
    academic_year_id = Column(UUID(as_uuid=True), ForeignKey("academic_years.id"))
    name             = Column(String(100), nullable=False)
    exam_type        = Column(String(50))
    start_date       = Column(Date)
    end_date         = Column(Date)
    is_published     = Column(Boolean, default=False)


class Mark(Base):
    __tablename__ = "marks"
    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    exam_id        = Column(UUID(as_uuid=True), ForeignKey("exams.id"))
    student_id     = Column(UUID(as_uuid=True), ForeignKey("students.id"))
    subject_id     = Column(UUID(as_uuid=True), ForeignKey("subjects.id"))
    marks_obtained = Column(Numeric(5, 2))
    max_marks      = Column(Numeric(5, 2), default=100)
    grade          = Column(String(5))
    remarks        = Column(Text)
    entered_by     = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    entered_at     = Column(DateTime(timezone=True), default=_now)

    __table_args__ = (
        UniqueConstraint("exam_id", "student_id", "subject_id"),
    )


# ── Fee Management ───────────────────────────────────────────────────────────

class FeeStructure(Base):
    __tablename__ = "fee_structure"
    id               = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id        = Column(UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False)
    academic_year_id = Column(UUID(as_uuid=True), ForeignKey("academic_years.id"))
    class_id         = Column(UUID(as_uuid=True), ForeignKey("classes.id"))
    fee_type         = Column(String(100), nullable=False)
    amount           = Column(Numeric(10, 2), nullable=False)
    due_date         = Column(Date)
    late_fine_per_day = Column(Numeric(6, 2), default=0)
    unlocks_premium   = Column(Boolean, default=False)
    premium_duration_days = Column(Integer)


class FeePayment(Base):
    __tablename__ = "fee_payments"
    id               = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id        = Column(UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False)
    student_id       = Column(UUID(as_uuid=True), ForeignKey("students.id"))
    fee_structure_id = Column(UUID(as_uuid=True), ForeignKey("fee_structure.id"))
    amount_paid      = Column(Numeric(10, 2))
    payment_date     = Column(DateTime(timezone=True), default=_now)
    payment_method   = Column(String(30))
    transaction_id   = Column(String(255))
    receipt_number   = Column(String(50), unique=True)
    status           = Column(String(20), default="pending")
    collected_by     = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    __table_args__ = (Index("ix_fee_payments_student", "student_id"),)


# ── Video LMS ────────────────────────────────────────────────────────────────

class VideoLesson(Base):
    __tablename__ = "video_lessons"
    id               = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id        = Column(UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False)
    subject_id       = Column(UUID(as_uuid=True), ForeignKey("subjects.id"))
    class_id         = Column(UUID(as_uuid=True), ForeignKey("classes.id"))
    teacher_id       = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    title            = Column(String(255), nullable=False)
    description      = Column(Text)
    chapter_name     = Column(String(100))
    topic_name       = Column(String(100))
    sequence_number  = Column(Integer)
    yt_video_id      = Column(String(50))
    yt_url           = Column(Text)
    yt_status        = Column(String(20), default="pending")
    yt_duration_secs = Column(Integer)
    cf_video_id      = Column(String(100))
    cf_status        = Column(String(20), default="pending")
    cf_hls_url       = Column(Text)
    cf_thumbnail_url = Column(Text)
    primary_player   = Column(String(10), default="youtube")
    thumbnail_url    = Column(Text)
    is_published     = Column(Boolean, default=False)
    is_premium       = Column(Boolean, default=False)
    is_free_preview  = Column(Boolean, default=False)
    view_count       = Column(Integer, default=0)
    created_at       = Column(DateTime(timezone=True), default=_now)
    updated_at       = Column(DateTime(timezone=True), default=_now, onupdate=_now)

    __table_args__ = (
        Index("ix_video_class", "class_id"),
        Index("ix_video_subject", "subject_id"),
    )


class VideoAttachment(Base):
    __tablename__ = "video_attachments"
    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    video_id       = Column(UUID(as_uuid=True), ForeignKey("video_lessons.id", ondelete="CASCADE"))
    title          = Column(String(255))
    file_type      = Column(String(20))
    file_url       = Column(Text, nullable=False)
    file_size_kb   = Column(Integer)
    is_premium     = Column(Boolean, default=False)
    is_active      = Column(Boolean, default=True)
    download_count = Column(Integer, default=0)
    created_at     = Column(DateTime(timezone=True), default=_now)


class VideoQuiz(Base):
    __tablename__ = "video_quizzes"
    id                = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    video_id          = Column(UUID(as_uuid=True), ForeignKey("video_lessons.id", ondelete="CASCADE"))
    title             = Column(String(255))
    time_limit_mins   = Column(Integer, default=10)
    pass_percentage   = Column(Integer, default=60)
    is_premium        = Column(Boolean, default=False)
    is_active         = Column(Boolean, default=True)
    created_at        = Column(DateTime(timezone=True), default=_now)


class QuizQuestion(Base):
    __tablename__ = "quiz_questions"
    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    quiz_id         = Column(UUID(as_uuid=True), ForeignKey("video_quizzes.id", ondelete="CASCADE"))
    question_text   = Column(Text, nullable=False)
    option_a        = Column(Text, nullable=False)
    option_b        = Column(Text, nullable=False)
    option_c        = Column(Text)
    option_d        = Column(Text)
    correct_option  = Column(String(1), nullable=False)
    explanation     = Column(Text)
    marks           = Column(Integer, default=1)
    sequence_number = Column(Integer)
    is_active       = Column(Boolean, default=True)


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"
    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    quiz_id        = Column(UUID(as_uuid=True), ForeignKey("video_quizzes.id"))
    student_id     = Column(UUID(as_uuid=True), ForeignKey("students.id"))
    started_at     = Column(DateTime(timezone=True), default=_now)
    submitted_at   = Column(DateTime(timezone=True))
    score          = Column(Numeric(5, 2))
    total_marks    = Column(Integer)
    percentage     = Column(Numeric(5, 2))
    is_passed      = Column(Boolean)
    is_invalidated = Column(Boolean, default=False)
    answers        = Column(JSONB)


class VideoProgress(Base):
    __tablename__ = "video_progress"
    id                    = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    video_id              = Column(UUID(as_uuid=True), ForeignKey("video_lessons.id"))
    student_id            = Column(UUID(as_uuid=True), ForeignKey("students.id"))
    watched_seconds       = Column(Integer, default=0)
    total_seconds         = Column(Integer)
    completion_percentage = Column(Numeric(5, 2), default=0)
    is_completed          = Column(Boolean, default=False)
    last_watched_at       = Column(DateTime(timezone=True), default=_now)

    __table_args__ = (
        UniqueConstraint("video_id", "student_id"),
        Index("ix_video_progress_student", "student_id"),
    )


# ── Notices ───────────────────────────────────────────────────────────────────

class Notice(Base):
    __tablename__ = "notices"
    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id       = Column(UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False)
    title           = Column(String(255), nullable=False)
    content         = Column(Text, nullable=False)
    target_audience = Column(String(30), default="all")
    class_id        = Column(UUID(as_uuid=True), ForeignKey("classes.id"))
    attachment_url  = Column(Text)
    is_published    = Column(Boolean, default=False)
    published_by    = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    published_at    = Column(DateTime(timezone=True))
    expires_at      = Column(DateTime(timezone=True))


# ── Homework ──────────────────────────────────────────────────────────────────

class Homework(Base):
    __tablename__ = "homework"
    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subject_id     = Column(UUID(as_uuid=True), ForeignKey("subjects.id"))
    class_id       = Column(UUID(as_uuid=True), ForeignKey("classes.id"))
    teacher_id     = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    title          = Column(String(255))
    description    = Column(Text)
    due_date       = Column(Date)
    attachment_url = Column(Text)
    created_at     = Column(DateTime(timezone=True), default=_now)


# ── Audit Log ─────────────────────────────────────────────────────────────────

class AuditLog(Base):
    __tablename__ = "audit_log"
    id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id  = Column(UUID(as_uuid=True), ForeignKey("schools.id"))
    user_id    = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    action     = Column(String(100), nullable=False)
    table_name = Column(String(100))
    record_id  = Column(UUID(as_uuid=True))
    old_values = Column(JSONB)
    new_values = Column(JSONB)
    ip_address = Column(INET)
    user_agent = Column(Text)
    created_at = Column(DateTime(timezone=True), default=_now)

    __table_args__ = (
        Index("ix_audit_user", "user_id"),
        Index("ix_audit_created", "created_at"),
    )


class ContentEditHistory(Base):
    __tablename__ = "content_edit_history"
    id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content_type  = Column(String(30))
    content_id    = Column(UUID(as_uuid=True))
    edited_by     = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    field_changed = Column(String(100))
    old_value     = Column(Text)
    new_value     = Column(Text)
    edited_at     = Column(DateTime(timezone=True), default=_now)
    ip_address    = Column(INET)


# ── Live Classes ──────────────────────────────────────────────────────────────

class LiveClass(Base):
    __tablename__ = "live_classes"
    id                  = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id           = Column(UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False)
    subject_id          = Column(UUID(as_uuid=True), ForeignKey("subjects.id"))
    class_id            = Column(UUID(as_uuid=True), ForeignKey("classes.id"))
    teacher_id          = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    title               = Column(String(255), nullable=False)
    scheduled_at        = Column(DateTime(timezone=True), nullable=False)
    duration_minutes    = Column(Integer, default=60)
    yt_live_stream_id   = Column(String(100))
    yt_broadcast_id     = Column(String(100))
    yt_watch_url        = Column(Text)
    yt_stream_key       = Column(Text)   # Encrypted
    status              = Column(String(20), default="scheduled")
    recording_video_id  = Column(UUID(as_uuid=True), ForeignKey("video_lessons.id"))
    created_at          = Column(DateTime(timezone=True), default=_now)
