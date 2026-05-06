"""
Video LMS API — YouTube link paste + Live class system
"""
import re
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from pydantic import BaseModel

from app.db.session import get_db
from app.core.security import require_roles
from app.models.models import (
    VideoLesson, VideoAttachment, VideoQuiz, QuizQuestion,
    QuizAttempt, VideoProgress, LiveClass, Class
)

router = APIRouter(prefix="/videos", tags=["videos"])
live_router = APIRouter(prefix="/live", tags=["live"])


def extract_yt_id(url: str) -> Optional[str]:
    patterns = [
        r'youtu\.be/([a-zA-Z0-9_-]{11})',
        r'youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})',
        r'youtube\.com/embed/([a-zA-Z0-9_-]{11})',
        r'youtube\.com/shorts/([a-zA-Z0-9_-]{11})',
        r'youtube\.com/live/([a-zA-Z0-9_-]{11})',
    ]
    for p in patterns:
        m = re.search(p, url)
        if m:
            return m.group(1)
    return None


def make_embed_url(yt_id: str) -> str:
    return f"https://www.youtube.com/embed/{yt_id}?modestbranding=1&rel=0&showinfo=0&cc_load_policy=1"


# Schemas
class VideoCreate(BaseModel):
    title: str
    description: Optional[str] = None
    yt_url: str
    subject_id: Optional[str] = None
    class_id: str
    chapter_name: Optional[str] = None
    topic_name: Optional[str] = None
    sequence_number: Optional[int] = None
    is_premium: bool = False
    is_free_preview: bool = False

class VideoUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    yt_url: Optional[str] = None
    chapter_name: Optional[str] = None
    topic_name: Optional[str] = None
    sequence_number: Optional[int] = None
    is_published: Optional[bool] = None
    is_premium: Optional[bool] = None
    is_free_preview: Optional[bool] = None
    primary_player: Optional[str] = None

class AttachmentCreate(BaseModel):
    title: str
    file_url: str
    file_type: str = "pdf"
    file_size_kb: Optional[int] = None
    is_premium: bool = False

class QuizCreate(BaseModel):
    title: str
    time_limit_mins: int = 10
    pass_percentage: int = 60
    is_premium: bool = False

class QuestionCreate(BaseModel):
    question_text: str
    option_a: str
    option_b: str
    option_c: Optional[str] = None
    option_d: Optional[str] = None
    correct_option: str
    explanation: Optional[str] = None
    marks: int = 1
    sequence_number: Optional[int] = None

class LiveClassCreate(BaseModel):
    title: str
    subject_id: Optional[str] = None
    class_id: str
    scheduled_at: datetime
    duration_minutes: int = 60
    yt_live_url: Optional[str] = None
    description: Optional[str] = None

class ProgressUpdate(BaseModel):
    watched_seconds: int
    total_seconds: int


@router.post("", status_code=201)
async def create_video(body: VideoCreate, db: AsyncSession = Depends(get_db),
    payload: dict = Depends(require_roles("teacher", "admin", "principal"))):
    school_id = payload["school_id"]
    yt_id = extract_yt_id(body.yt_url)
    if not yt_id:
        raise HTTPException(400, "Invalid YouTube URL. Example: https://www.youtube.com/watch?v=XXXXXXXXXXX")
    cls = (await db.execute(select(Class).where(Class.id == body.class_id, Class.school_id == school_id))).scalar_one_or_none()
    if not cls:
        raise HTTPException(404, "Class not found")
    video = VideoLesson(
        school_id=school_id, subject_id=body.subject_id, class_id=body.class_id,
        teacher_id=payload["sub"], title=body.title, description=body.description,
        chapter_name=body.chapter_name, topic_name=body.topic_name,
        sequence_number=body.sequence_number, yt_video_id=yt_id, yt_url=body.yt_url,
        yt_status="ready", primary_player="youtube", is_published=False,
        is_premium=body.is_premium, is_free_preview=body.is_free_preview,
        thumbnail_url=f"https://img.youtube.com/vi/{yt_id}/mqdefault.jpg",
    )
    db.add(video)
    await db.flush()
    return {"id": str(video.id), "yt_video_id": yt_id, "embed_url": make_embed_url(yt_id),
            "thumbnail_url": video.thumbnail_url, "message": "Video added. Publish when ready."}


@router.get("")
async def list_videos(class_id: Optional[str] = Query(None), subject_id: Optional[str] = Query(None),
    chapter_name: Optional[str] = Query(None), is_published: Optional[bool] = Query(None),
    page: int = Query(1, ge=1), per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(require_roles("admin", "principal", "teacher", "student", "parent"))):
    school_id = payload["school_id"]
    role = payload["role"]
    query = select(VideoLesson).where(VideoLesson.school_id == school_id)
    if role in ["student", "parent"]:
        query = query.where(VideoLesson.is_published == True)
    elif is_published is not None:
        query = query.where(VideoLesson.is_published == is_published)
    if class_id: query = query.where(VideoLesson.class_id == class_id)
    if subject_id: query = query.where(VideoLesson.subject_id == subject_id)
    if chapter_name: query = query.where(VideoLesson.chapter_name == chapter_name)
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    query = query.order_by(VideoLesson.chapter_name, VideoLesson.sequence_number, VideoLesson.created_at)
    query = query.offset((page - 1) * per_page).limit(per_page)
    videos = (await db.execute(query)).scalars().all()
    return {
        "items": [{"id": str(v.id), "title": v.title, "description": v.description,
                   "chapter_name": v.chapter_name, "topic_name": v.topic_name,
                   "sequence_number": v.sequence_number, "thumbnail_url": v.thumbnail_url,
                   "is_published": v.is_published, "is_premium": v.is_premium,
                   "is_free_preview": v.is_free_preview, "view_count": v.view_count,
                   "yt_video_id": v.yt_video_id if role in ["teacher","admin","principal"] else None,
                   "created_at": v.created_at.isoformat() if v.created_at else None}
                  for v in videos],
        "total": total, "page": page, "pages": (total + per_page - 1) // per_page,
    }


@router.get("/{video_id}/player-token")
async def get_player_token(video_id: str, db: AsyncSession = Depends(get_db),
    payload: dict = Depends(require_roles("admin", "principal", "teacher", "student", "parent"))):
    """6-layer server-side access control"""
    school_id = payload["school_id"]
    role = payload["role"]
    video = (await db.execute(select(VideoLesson).where(VideoLesson.id == video_id, VideoLesson.school_id == school_id))).scalar_one_or_none()
    if not video: raise HTTPException(404, "Video not found")
    if role in ["student", "parent"] and not video.is_published: raise HTTPException(404, "Video not found")
    if role == "student":
        from app.models.models import Student
        student = (await db.execute(select(Student).where(Student.user_id == payload["sub"], Student.school_id == school_id))).scalar_one_or_none()
        if not student: raise HTTPException(403, "Student record not found")
        if str(student.class_id) != str(video.class_id): raise HTTPException(403, "This video is not for your class")
        if video.is_premium and not video.is_free_preview and not student.is_premium:
            raise HTTPException(402, {"error": "premium_required", "message": "Contact school admin to activate premium"})
    await db.execute(update(VideoLesson).where(VideoLesson.id == video_id).values(view_count=VideoLesson.view_count + 1))
    return {
        "video_id": str(video.id), "title": video.title, "description": video.description,
        "embed_url": make_embed_url(video.yt_video_id),
        "thumbnail_url": video.thumbnail_url, "is_premium": video.is_premium,
        "chapter_name": video.chapter_name, "topic_name": video.topic_name,
        "cf_embed_url": f"https://iframe.cloudflarestream.com/{video.cf_video_id}" if video.cf_video_id else None,
        "primary_player": video.primary_player,
    }


@router.patch("/{video_id}")
async def update_video(video_id: str, body: VideoUpdate, db: AsyncSession = Depends(get_db),
    payload: dict = Depends(require_roles("teacher", "admin", "principal"))):
    school_id = payload["school_id"]
    video = (await db.execute(select(VideoLesson).where(VideoLesson.id == video_id, VideoLesson.school_id == school_id))).scalar_one_or_none()
    if not video: raise HTTPException(404, "Video not found")
    if payload["role"] == "teacher" and str(video.teacher_id) != payload["sub"]: raise HTTPException(403, "You can only edit your own videos")
    data = body.model_dump(exclude_unset=True)
    if "yt_url" in data:
        new_id = extract_yt_id(data["yt_url"])
        if not new_id: raise HTTPException(400, "Invalid YouTube URL")
        video.yt_video_id = new_id
        video.thumbnail_url = f"https://img.youtube.com/vi/{new_id}/mqdefault.jpg"
        video.yt_url = data.pop("yt_url")
    for k, v in data.items():
        if hasattr(video, k): setattr(video, k, v)
    return {"message": "Video updated", "yt_video_id": video.yt_video_id, "embed_url": make_embed_url(video.yt_video_id)}


@router.delete("/{video_id}")
async def delete_video(video_id: str, db: AsyncSession = Depends(get_db),
    payload: dict = Depends(require_roles("teacher", "admin"))):
    school_id = payload["school_id"]
    video = (await db.execute(select(VideoLesson).where(VideoLesson.id == video_id, VideoLesson.school_id == school_id))).scalar_one_or_none()
    if not video: raise HTTPException(404, "Video not found")
    if payload["role"] == "teacher" and str(video.teacher_id) != payload["sub"]: raise HTTPException(403, "You can only delete your own videos")
    if payload["role"] == "teacher":
        video.is_published = False
        return {"message": "Video unpublished"}
    await db.delete(video)
    return {"message": "Video deleted"}


@router.post("/{video_id}/progress")
async def update_progress(video_id: str, body: ProgressUpdate, db: AsyncSession = Depends(get_db),
    payload: dict = Depends(require_roles("student"))):
    from app.models.models import Student
    student = (await db.execute(select(Student).where(Student.user_id == payload["sub"], Student.school_id == payload["school_id"]))).scalar_one_or_none()
    if not student: raise HTTPException(404, "Student not found")
    pct = round(body.watched_seconds / body.total_seconds * 100, 1) if body.total_seconds > 0 else 0
    existing = (await db.execute(select(VideoProgress).where(VideoProgress.video_id == video_id, VideoProgress.student_id == student.id))).scalar_one_or_none()
    if existing:
        existing.watched_seconds = max(existing.watched_seconds, body.watched_seconds)
        existing.total_seconds = body.total_seconds
        existing.completion_percentage = pct
        existing.is_completed = pct >= 80
        existing.last_watched_at = datetime.now(timezone.utc)
    else:
        db.add(VideoProgress(video_id=video_id, student_id=student.id, watched_seconds=body.watched_seconds, total_seconds=body.total_seconds, completion_percentage=pct, is_completed=pct >= 80))
    return {"completion_percentage": pct, "is_completed": pct >= 80}


@router.post("/{video_id}/attachments", status_code=201)
async def add_attachment(video_id: str, body: AttachmentCreate, db: AsyncSession = Depends(get_db),
    payload: dict = Depends(require_roles("teacher", "admin"))):
    video = (await db.execute(select(VideoLesson).where(VideoLesson.id == video_id, VideoLesson.school_id == payload["school_id"]))).scalar_one_or_none()
    if not video: raise HTTPException(404, "Video not found")
    att = VideoAttachment(video_id=video_id, title=body.title, file_type=body.file_type, file_url=body.file_url, file_size_kb=body.file_size_kb, is_premium=body.is_premium)
    db.add(att)
    await db.flush()
    return {"id": str(att.id), "message": "Attachment added"}


@router.get("/{video_id}/attachments")
async def list_attachments(video_id: str, db: AsyncSession = Depends(get_db),
    payload: dict = Depends(require_roles("admin", "principal", "teacher", "student"))):
    atts = (await db.execute(select(VideoAttachment).where(VideoAttachment.video_id == video_id, VideoAttachment.is_active == True))).scalars().all()
    return [{"id": str(a.id), "title": a.title, "file_type": a.file_type, "file_size_kb": a.file_size_kb, "is_premium": a.is_premium} for a in atts]


@router.delete("/{video_id}/attachments/{att_id}")
async def delete_attachment(video_id: str, att_id: str, db: AsyncSession = Depends(get_db),
    payload: dict = Depends(require_roles("teacher", "admin"))):
    att = (await db.execute(select(VideoAttachment).where(VideoAttachment.id == att_id))).scalar_one_or_none()
    if not att: raise HTTPException(404, "Attachment not found")
    att.is_active = False
    return {"message": "Attachment removed"}


@router.post("/{video_id}/quiz", status_code=201)
async def create_quiz(video_id: str, body: QuizCreate, db: AsyncSession = Depends(get_db),
    payload: dict = Depends(require_roles("teacher", "admin"))):
    quiz = VideoQuiz(video_id=video_id, title=body.title, time_limit_mins=body.time_limit_mins, pass_percentage=body.pass_percentage, is_premium=body.is_premium)
    db.add(quiz)
    await db.flush()
    return {"id": str(quiz.id), "message": "Quiz created"}


@router.post("/quiz/{quiz_id}/questions", status_code=201)
async def add_question(quiz_id: str, body: QuestionCreate, db: AsyncSession = Depends(get_db),
    payload: dict = Depends(require_roles("teacher", "admin"))):
    if body.correct_option not in ['a','b','c','d']: raise HTTPException(400, "correct_option must be a, b, c, or d")
    q = QuizQuestion(quiz_id=quiz_id, question_text=body.question_text, option_a=body.option_a, option_b=body.option_b, option_c=body.option_c, option_d=body.option_d, correct_option=body.correct_option, explanation=body.explanation, marks=body.marks, sequence_number=body.sequence_number)
    db.add(q)
    await db.flush()
    return {"id": str(q.id), "message": "Question added"}


@router.get("/quiz/{quiz_id}/attempt")
async def start_quiz(quiz_id: str, db: AsyncSession = Depends(get_db),
    payload: dict = Depends(require_roles("student"))):
    quiz = (await db.execute(select(VideoQuiz).where(VideoQuiz.id == quiz_id, VideoQuiz.is_active == True))).scalar_one_or_none()
    if not quiz: raise HTTPException(404, "Quiz not found")
    questions = (await db.execute(select(QuizQuestion).where(QuizQuestion.quiz_id == quiz_id, QuizQuestion.is_active == True).order_by(QuizQuestion.sequence_number))).scalars().all()
    return {"quiz_id": str(quiz.id), "title": quiz.title, "time_limit_mins": quiz.time_limit_mins, "total_questions": len(questions),
            "questions": [{"id": str(q.id), "question_text": q.question_text, "option_a": q.option_a, "option_b": q.option_b, "option_c": q.option_c, "option_d": q.option_d, "marks": q.marks} for q in questions]}


@router.post("/quiz/{quiz_id}/submit")
async def submit_quiz(quiz_id: str, answers: dict, db: AsyncSession = Depends(get_db),
    payload: dict = Depends(require_roles("student"))):
    from app.models.models import Student
    student = (await db.execute(select(Student).where(Student.user_id == payload["sub"], Student.school_id == payload["school_id"]))).scalar_one_or_none()
    if not student: raise HTTPException(404, "Student not found")
    quiz = (await db.execute(select(VideoQuiz).where(VideoQuiz.id == quiz_id))).scalar_one_or_none()
    if not quiz: raise HTTPException(404, "Quiz not found")
    questions = (await db.execute(select(QuizQuestion).where(QuizQuestion.quiz_id == quiz_id, QuizQuestion.is_active == True))).scalars().all()
    total_marks = sum(q.marks for q in questions)
    scored = 0
    results = []
    for q in questions:
        selected = answers.get(str(q.id), "").lower()
        is_correct = selected == q.correct_option
        if is_correct: scored += q.marks
        results.append({"question_id": str(q.id), "question_text": q.question_text, "selected": selected, "correct": q.correct_option, "is_correct": is_correct, "explanation": q.explanation})
    percentage = round(scored / total_marks * 100, 1) if total_marks > 0 else 0
    is_passed = percentage >= quiz.pass_percentage
    db.add(QuizAttempt(quiz_id=quiz_id, student_id=student.id, submitted_at=datetime.now(timezone.utc), score=scored, total_marks=total_marks, percentage=percentage, is_passed=is_passed, answers=answers))
    return {"score": scored, "total_marks": total_marks, "percentage": percentage, "is_passed": is_passed, "pass_percentage": quiz.pass_percentage, "results": results}


# LIVE
@live_router.post("", status_code=201)
async def schedule_live(body: LiveClassCreate, db: AsyncSession = Depends(get_db),
    payload: dict = Depends(require_roles("teacher", "admin", "principal"))):
    school_id = payload["school_id"]
    cls = (await db.execute(select(Class).where(Class.id == body.class_id, Class.school_id == school_id))).scalar_one_or_none()
    if not cls: raise HTTPException(404, "Class not found")
    yt_broadcast_id = None
    if body.yt_live_url:
        yt_broadcast_id = extract_yt_id(body.yt_live_url)
        if not yt_broadcast_id: raise HTTPException(400, "Invalid YouTube Live URL")
    live = LiveClass(school_id=school_id, subject_id=body.subject_id, class_id=body.class_id,
                     teacher_id=payload["sub"], title=body.title, scheduled_at=body.scheduled_at,
                     duration_minutes=body.duration_minutes, yt_broadcast_id=yt_broadcast_id,
                     yt_watch_url=body.yt_live_url, status="scheduled")
    db.add(live)
    await db.flush()
    return {"id": str(live.id), "message": "Live class scheduled", "embed_url": make_embed_url(yt_broadcast_id) if yt_broadcast_id else None}


@live_router.get("")
async def list_live(class_id: Optional[str] = Query(None), status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(require_roles("admin", "principal", "teacher", "student", "parent"))):
    school_id = payload["school_id"]
    query = select(LiveClass).where(LiveClass.school_id == school_id)
    if class_id: query = query.where(LiveClass.class_id == class_id)
    if status: query = query.where(LiveClass.status == status)
    elif payload["role"] in ["student", "parent"]: query = query.where(LiveClass.status.in_(["scheduled", "live"]))
    classes = (await db.execute(query.order_by(LiveClass.scheduled_at.desc()).limit(50))).scalars().all()
    return [{"id": str(lc.id), "title": lc.title, "scheduled_at": lc.scheduled_at.isoformat(),
             "duration_minutes": lc.duration_minutes, "status": lc.status, "is_live_now": lc.status == "live",
             "embed_url": make_embed_url(lc.yt_broadcast_id) if lc.yt_broadcast_id and lc.status in ["live","scheduled"] else None}
            for lc in classes]


@live_router.patch("/{live_id}/status")
async def update_live_status(live_id: str, status: str, db: AsyncSession = Depends(get_db),
    payload: dict = Depends(require_roles("teacher", "admin"))):
    if status not in ["live", "ended", "scheduled"]: raise HTTPException(400, "Invalid status")
    lc = (await db.execute(select(LiveClass).where(LiveClass.id == live_id, LiveClass.school_id == payload["school_id"]))).scalar_one_or_none()
    if not lc: raise HTTPException(404, "Live class not found")
    lc.status = status
    return {"message": f"Status updated to '{status}'"}


@live_router.patch("/{live_id}/url")
async def update_live_url(live_id: str, yt_live_url: str, db: AsyncSession = Depends(get_db),
    payload: dict = Depends(require_roles("teacher", "admin"))):
    yt_id = extract_yt_id(yt_live_url)
    if not yt_id: raise HTTPException(400, "Invalid YouTube Live URL")
    lc = (await db.execute(select(LiveClass).where(LiveClass.id == live_id, LiveClass.school_id == payload["school_id"]))).scalar_one_or_none()
    if not lc: raise HTTPException(404, "Live class not found")
    lc.yt_broadcast_id = yt_id
    lc.yt_watch_url = yt_live_url
    return {"message": "Live URL updated", "embed_url": make_embed_url(yt_id)}
