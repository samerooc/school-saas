"""
Pydantic v2 Schemas — Request/Response models
"""
from pydantic import BaseModel, EmailStr, field_validator, model_validator
from typing import Optional, List
from datetime import date, datetime
from uuid import UUID
import re


# ── Shared ────────────────────────────────────────────────────────────────────

class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int
    per_page: int
    pages: int


# ── Academic Year ─────────────────────────────────────────────────────────────

class AcademicYearCreate(BaseModel):
    year_label: str          # "2024-2025"
    start_date: date
    end_date: date
    is_current: bool = False

class AcademicYearOut(BaseModel):
    id: UUID
    year_label: str
    start_date: date
    end_date: date
    is_current: bool
    model_config = {"from_attributes": True}


# ── Class ─────────────────────────────────────────────────────────────────────

class ClassCreate(BaseModel):
    name: str                        # "Class 10"
    section: Optional[str] = None   # "A"
    academic_year_id: UUID
    class_teacher_id: Optional[UUID] = None
    room_number: Optional[str] = None
    max_students: int = 40

class ClassUpdate(BaseModel):
    name: Optional[str] = None
    section: Optional[str] = None
    class_teacher_id: Optional[UUID] = None
    room_number: Optional[str] = None
    max_students: Optional[int] = None

class ClassOut(BaseModel):
    id: UUID
    name: str
    section: Optional[str]
    room_number: Optional[str]
    max_students: int
    class_teacher_name: Optional[str] = None
    student_count: int = 0
    model_config = {"from_attributes": True}


# ── Subject ───────────────────────────────────────────────────────────────────

class SubjectCreate(BaseModel):
    name: str
    code: Optional[str] = None
    class_id: UUID
    teacher_id: Optional[UUID] = None
    max_marks: int = 100

class SubjectOut(BaseModel):
    id: UUID
    name: str
    code: Optional[str]
    max_marks: int
    teacher_name: Optional[str] = None
    model_config = {"from_attributes": True}


# ── Student ───────────────────────────────────────────────────────────────────

class StudentCreate(BaseModel):
    full_name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    class_id: UUID
    roll_number: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    blood_group: Optional[str] = None
    address: Optional[str] = None
    parent_id: Optional[UUID] = None
    # Parent details (if new parent)
    parent_name: Optional[str] = None
    parent_email: Optional[EmailStr] = None
    parent_phone: Optional[str] = None

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, v):
        if v and v not in ["male", "female", "other"]:
            raise ValueError("Gender must be male, female, or other")
        return v

class StudentUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    class_id: Optional[UUID] = None
    roll_number: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    blood_group: Optional[str] = None
    address: Optional[str] = None
    is_active: Optional[bool] = None

class StudentOut(BaseModel):
    id: UUID
    user_id: Optional[UUID]
    admission_number: str
    roll_number: Optional[str]
    full_name: str
    email: Optional[str]
    phone: Optional[str]
    class_name: Optional[str] = None
    section: Optional[str] = None
    date_of_birth: Optional[date]
    gender: Optional[str]
    blood_group: Optional[str]
    address: Optional[str]
    photo_url: Optional[str]
    is_active: bool
    is_premium: bool
    admission_date: Optional[date]
    parent_name: Optional[str] = None
    parent_phone: Optional[str] = None
    model_config = {"from_attributes": True}

class StudentListItem(BaseModel):
    id: UUID
    admission_number: str
    full_name: str
    class_name: Optional[str] = None
    section: Optional[str] = None
    roll_number: Optional[str]
    is_active: bool
    is_premium: bool
    photo_url: Optional[str]
    model_config = {"from_attributes": True}


# ── Staff ─────────────────────────────────────────────────────────────────────

class StaffCreate(BaseModel):
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    role: str = "teacher"
    designation: Optional[str] = None
    department: Optional[str] = None
    qualification: Optional[str] = None
    salary: Optional[float] = None
    joining_date: Optional[date] = None
    subjects: Optional[List[str]] = None

    @field_validator("role")
    @classmethod
    def validate_role(cls, v):
        if v not in ["teacher", "principal", "admin"]:
            raise ValueError("Role must be teacher, principal, or admin")
        return v

class StaffUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    designation: Optional[str] = None
    department: Optional[str] = None
    qualification: Optional[str] = None
    salary: Optional[float] = None
    subjects: Optional[List[str]] = None
    is_active: Optional[bool] = None

class StaffOut(BaseModel):
    id: UUID
    user_id: UUID
    employee_id: str
    full_name: str
    email: str
    phone: Optional[str]
    role: str
    designation: Optional[str]
    department: Optional[str]
    qualification: Optional[str]
    subjects: Optional[List[str]]
    joining_date: Optional[date]
    is_active: bool
    model_config = {"from_attributes": True}


# ── Attendance ────────────────────────────────────────────────────────────────

class AttendanceEntry(BaseModel):
    student_id: UUID
    status: str   # present | absent | late | holiday

    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        if v not in ["present", "absent", "late", "holiday"]:
            raise ValueError("Invalid status")
        return v

class AttendanceBulkCreate(BaseModel):
    class_id: UUID
    date: date
    entries: List[AttendanceEntry]

class AttendanceOut(BaseModel):
    student_id: UUID
    student_name: str
    date: date
    status: str
    model_config = {"from_attributes": True}


# ── Homework ──────────────────────────────────────────────────────────────────

class HomeworkCreate(BaseModel):
    subject_id: UUID
    class_id: UUID
    title: str
    description: Optional[str] = None
    due_date: date

class HomeworkOut(BaseModel):
    id: UUID
    title: str
    description: Optional[str]
    due_date: date
    subject_name: Optional[str] = None
    teacher_name: Optional[str] = None
    attachment_url: Optional[str]
    created_at: datetime
    model_config = {"from_attributes": True}


# ── Notice ────────────────────────────────────────────────────────────────────

class NoticeCreate(BaseModel):
    title: str
    content: str
    target_audience: str = "all"   # all | students | teachers | parents
    class_id: Optional[UUID] = None
    expires_at: Optional[datetime] = None

    @field_validator("target_audience")
    @classmethod
    def validate_audience(cls, v):
        if v not in ["all", "students", "teachers", "parents"]:
            raise ValueError("Invalid target audience")
        return v

class NoticeOut(BaseModel):
    id: UUID
    title: str
    content: str
    target_audience: str
    is_published: bool
    published_at: Optional[datetime]
    expires_at: Optional[datetime]
    published_by_name: Optional[str] = None
    model_config = {"from_attributes": True}
