"""
Exams & Marks API - Module 4 (Enhanced)
- Exam schedule with subjects
- Bulk marks entry per class
- Results with grade calculation
- Marksheet PDF generation
- Class-wise result report
"""
from typing import Optional, List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import io

from app.db.session import get_db
from app.core.security import require_roles, get_current_user_payload
from app.models.models import Exam, Mark, Subject, Student, User, Class

router = APIRouter(prefix="/exams", tags=["exams"])


def calculate_grade(marks: float, max_marks: float) -> str:
    pct = (marks / max_marks * 100) if max_marks > 0 else 0
    if pct >= 90: return "A+"
    if pct >= 80: return "A"
    if pct >= 70: return "B+"
    if pct >= 60: return "B"
    if pct >= 50: return "C"
    if pct >= 40: return "D"
    return "F"


# ── Exam CRUD ─────────────────────────────────────────────────────────────────

@router.post("", status_code=201)
async def create_exam(
    name: str,
    academic_year_id: str,
    exam_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(require_roles("admin", "principal")),
):
    school_id = payload["school_id"]
    exam = Exam(
        school_id=school_id, academic_year_id=academic_year_id,
        name=name, exam_type=exam_type,
        start_date=start_date, end_date=end_date, is_published=False,
    )
    db.add(exam)
    await db.flush()
    return {"id": str(exam.id), "message": "Exam created"}


@router.get("")
async def list_exams(
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(get_current_user_payload),
):
    school_id = payload["school_id"]
    result = await db.execute(
        select(Exam).where(Exam.school_id == school_id).order_by(Exam.start_date.desc())
    )
    return [
        {"id": str(e.id), "name": e.name, "exam_type": e.exam_type,
         "start_date": str(e.start_date) if e.start_date else None,
         "end_date": str(e.end_date) if e.end_date else None,
         "is_published": e.is_published}
        for e in result.scalars().all()
    ]


@router.patch("/{exam_id}/publish")
async def publish_exam(
    exam_id: str,
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(require_roles("admin", "principal")),
):
    school_id = payload["school_id"]
    exam = (await db.execute(
        select(Exam).where(Exam.id == exam_id, Exam.school_id == school_id)
    )).scalar_one_or_none()
    if not exam: raise HTTPException(404, "Exam not found")
    exam.is_published = True
    return {"message": "Results published. Students can now view their marksheet."}


# ── Marks Entry ───────────────────────────────────────────────────────────────

@router.post("/{exam_id}/marks", status_code=201)
async def enter_marks(
    exam_id: str,
    marks_list: List[dict],
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(require_roles("teacher", "admin")),
):
    """
    marks_list = [{"student_id": "...", "subject_id": "...", "marks_obtained": 85}]
    Server calculates grade — never trust client-submitted grades.
    """
    school_id = payload["school_id"]
    exam = (await db.execute(
        select(Exam).where(Exam.id == exam_id, Exam.school_id == school_id)
    )).scalar_one_or_none()
    if not exam: raise HTTPException(404, "Exam not found")
    if exam.is_published:
        raise HTTPException(400, "Cannot edit marks after results are published")

    saved = 0
    for entry in marks_list:
        sid = entry.get("student_id")
        subid = entry.get("subject_id")
        mo = entry.get("marks_obtained")
        if not all([sid, subid, mo is not None]): continue

        sub = (await db.execute(
            select(Subject).where(Subject.id == subid, Subject.school_id == school_id)
        )).scalar_one_or_none()
        max_m = float(sub.max_marks) if sub else 100.0
        grade = calculate_grade(float(mo), max_m)

        existing = (await db.execute(
            select(Mark).where(Mark.exam_id == exam_id, Mark.student_id == sid, Mark.subject_id == subid)
        )).scalar_one_or_none()

        if existing:
            existing.marks_obtained = mo
            existing.grade = grade
            existing.entered_by = payload["sub"]
        else:
            db.add(Mark(exam_id=exam_id, student_id=sid, subject_id=subid,
                        marks_obtained=mo, max_marks=max_m, grade=grade, entered_by=payload["sub"]))
        saved += 1

    return {"message": f"{saved} marks saved"}


@router.get("/{exam_id}/marks/class/{class_id}")
async def get_class_marks_entry(
    exam_id: str,
    class_id: str,
    subject_id: str,
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(require_roles("teacher", "admin")),
):
    """Load current marks for a class/subject — for teacher to fill/edit"""
    school_id = payload["school_id"]

    students = (await db.execute(
        select(Student, User)
        .join(User, User.id == Student.user_id, isouter=True)
        .where(Student.class_id == class_id, Student.school_id == school_id, Student.is_active == True)
        .order_by(Student.roll_number)
    )).all()

    result = []
    for student, user in students:
        mark = (await db.execute(
            select(Mark).where(Mark.exam_id == exam_id, Mark.student_id == student.id, Mark.subject_id == subject_id)
        )).scalar_one_or_none()
        result.append({
            "student_id": str(student.id),
            "student_name": user.full_name if user else "Unknown",
            "roll_number": student.roll_number,
            "marks_obtained": float(mark.marks_obtained) if mark else None,
            "grade": mark.grade if mark else None,
        })
    return result


# ── Results ───────────────────────────────────────────────────────────────────

@router.get("/{exam_id}/results/{student_id}")
async def get_student_results(
    exam_id: str, student_id: str,
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(get_current_user_payload),
):
    school_id = payload["school_id"]
    exam = (await db.execute(
        select(Exam).where(Exam.id == exam_id, Exam.school_id == school_id)
    )).scalar_one_or_none()
    if not exam: raise HTTPException(404, "Exam not found")

    if payload["role"] == "student":
        if not exam.is_published:
            raise HTTPException(403, "Results not published yet")
        own = (await db.execute(
            select(Student).where(Student.user_id == payload["sub"], Student.school_id == school_id)
        )).scalar_one_or_none()
        if not own or str(own.id) != student_id:
            raise HTTPException(403, "You can only view your own results")

    rows = (await db.execute(
        select(Mark, Subject)
        .join(Subject, Subject.id == Mark.subject_id, isouter=True)
        .where(Mark.exam_id == exam_id, Mark.student_id == student_id)
        .order_by(Subject.name)
    )).all()

    total_obtained = sum(float(m.marks_obtained or 0) for m, _ in rows)
    total_max = sum(float(m.max_marks or 100) for m, _ in rows)
    pct = round(total_obtained / total_max * 100, 1) if total_max > 0 else 0

    return {
        "exam_name": exam.name,
        "student_id": student_id,
        "subjects": [
            {"subject_name": sub.name if sub else "?",
             "marks_obtained": float(m.marks_obtained or 0),
             "max_marks": float(m.max_marks or 100),
             "grade": m.grade,
             "percentage": round(float(m.marks_obtained or 0) / float(m.max_marks or 100) * 100, 1)}
            for m, sub in rows
        ],
        "total_obtained": total_obtained,
        "total_max": total_max,
        "overall_percentage": pct,
        "overall_grade": calculate_grade(pct, 100),
        "result": "PASS" if pct >= 33 else "FAIL",
    }


@router.get("/{exam_id}/results/class/{class_id}")
async def get_class_results(
    exam_id: str, class_id: str,
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(require_roles("teacher", "admin", "principal")),
):
    """Class-wise result summary — rank list"""
    school_id = payload["school_id"]
    exam = (await db.execute(
        select(Exam).where(Exam.id == exam_id, Exam.school_id == school_id)
    )).scalar_one_or_none()
    if not exam: raise HTTPException(404, "Exam not found")

    students = (await db.execute(
        select(Student, User)
        .join(User, User.id == Student.user_id, isouter=True)
        .where(Student.class_id == class_id, Student.school_id == school_id, Student.is_active == True)
    )).all()

    results = []
    for student, user in students:
        marks = (await db.execute(
            select(Mark).where(Mark.exam_id == exam_id, Mark.student_id == student.id)
        )).scalars().all()
        if not marks: continue
        total_o = sum(float(m.marks_obtained or 0) for m in marks)
        total_m = sum(float(m.max_marks or 100) for m in marks)
        pct = round(total_o / total_m * 100, 1) if total_m > 0 else 0
        results.append({
            "student_id": str(student.id),
            "student_name": user.full_name if user else "?",
            "roll_number": student.roll_number,
            "total_obtained": total_o,
            "total_max": total_m,
            "percentage": pct,
            "grade": calculate_grade(pct, 100),
            "result": "PASS" if pct >= 33 else "FAIL",
        })

    # Sort by percentage descending → add rank
    results.sort(key=lambda x: x["percentage"], reverse=True)
    for i, r in enumerate(results, 1):
        r["rank"] = i

    return {"exam_name": exam.name, "class_id": class_id, "students": results}


# ── Marksheet PDF ─────────────────────────────────────────────────────────────

@router.get("/{exam_id}/marksheet/{student_id}/pdf")
async def download_marksheet_pdf(
    exam_id: str, student_id: str,
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(get_current_user_payload),
):
    """
    Generate marksheet PDF server-side.
    Student can only download their own.
    PDF generated with reportlab — never trust client data.
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.units import cm
    except ImportError:
        raise HTTPException(500, "reportlab not installed. Run: pip install reportlab")

    school_id = payload["school_id"]

    # Security checks
    exam = (await db.execute(
        select(Exam).where(Exam.id == exam_id, Exam.school_id == school_id)
    )).scalar_one_or_none()
    if not exam: raise HTTPException(404, "Exam not found")

    if payload["role"] == "student":
        if not exam.is_published:
            raise HTTPException(403, "Results not yet published")
        own = (await db.execute(
            select(Student).where(Student.user_id == payload["sub"], Student.school_id == school_id)
        )).scalar_one_or_none()
        if not own or str(own.id) != student_id:
            raise HTTPException(403, "You can only download your own marksheet")

    # Fetch student info
    student_row = (await db.execute(
        select(Student, User)
        .join(User, User.id == Student.user_id, isouter=True)
        .where(Student.id == student_id, Student.school_id == school_id)
    )).first()
    if not student_row: raise HTTPException(404, "Student not found")
    student, user = student_row

    # Fetch class info
    cls = (await db.execute(select(Class).where(Class.id == student.class_id))).scalar_one_or_none()

    # Fetch marks
    marks_rows = (await db.execute(
        select(Mark, Subject)
        .join(Subject, Subject.id == Mark.subject_id, isouter=True)
        .where(Mark.exam_id == exam_id, Mark.student_id == student_id)
        .order_by(Subject.name)
    )).all()

    total_o = sum(float(m.marks_obtained or 0) for m, _ in marks_rows)
    total_m = sum(float(m.max_marks or 100) for m, _ in marks_rows)
    pct = round(total_o / total_m * 100, 1) if total_m > 0 else 0
    overall_grade = calculate_grade(pct, 100)
    result_status = "PASS" if pct >= 33 else "FAIL"

    # ── Build PDF ──────────────────────────────────────────────────────────────
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=1.5*cm, bottomMargin=1.5*cm, leftMargin=2*cm, rightMargin=2*cm)
    styles = getSampleStyleSheet()
    story = []

    # Header
    story.append(Paragraph("<b>SCHOOL NAME</b>", ParagraphStyle("title", fontSize=18, spaceAfter=4, alignment=1)))
    story.append(Paragraph("Progress Report / Marksheet", ParagraphStyle("sub", fontSize=12, spaceAfter=2, alignment=1, textColor=colors.grey)))
    story.append(Spacer(1, 0.4*cm))

    # Exam name
    story.append(Paragraph(f"<b>{exam.name}</b>", ParagraphStyle("exam", fontSize=13, spaceAfter=12, alignment=1, textColor=colors.HexColor("#4f46e5"))))

    # Student info table
    cls_name = f"{cls.name}{' - ' + cls.section if cls and cls.section else ''}" if cls else "N/A"
    info_data = [
        ["Student Name:", user.full_name if user else "N/A", "Admission No:", student.admission_number],
        ["Class:", cls_name, "Roll No:", student.roll_number or "N/A"],
    ]
    info_table = Table(info_data, colWidths=[3.5*cm, 6*cm, 3.5*cm, 4*cm])
    info_table.setStyle(TableStyle([
        ("FONTSIZE", (0,0), (-1,-1), 10),
        ("FONTNAME", (0,0), (0,-1), "Helvetica-Bold"),
        ("FONTNAME", (2,0), (2,-1), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ("TOPPADDING", (0,0), (-1,-1), 6),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 0.5*cm))

    # Marks table
    headers = ["Subject", "Max Marks", "Marks Obtained", "Grade", "Percentage"]
    data = [headers]
    for mark, sub in marks_rows:
        mo = float(mark.marks_obtained or 0)
        mm = float(mark.max_marks or 100)
        sp = round(mo / mm * 100, 1) if mm > 0 else 0
        data.append([
            sub.name if sub else "?",
            str(int(mm)),
            str(int(mo)),
            mark.grade or "?",
            f"{sp}%",
        ])

    # Total row
    data.append(["TOTAL", str(int(total_m)), str(int(total_o)), overall_grade, f"{pct}%"])

    marks_table = Table(data, colWidths=[5.5*cm, 3*cm, 3.5*cm, 2.5*cm, 3*cm])
    marks_table.setStyle(TableStyle([
        # Header row
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#4f46e5")),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 10),
        ("ALIGN", (1,0), (-1,-1), "CENTER"),
        ("ROWBACKGROUNDS", (0,1), (-1,-2), [colors.white, colors.HexColor("#f8f8ff")]),
        # Total row
        ("BACKGROUND", (0,-1), (-1,-1), colors.HexColor("#e0e7ff")),
        ("FONTNAME", (0,-1), (-1,-1), "Helvetica-Bold"),
        ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#d1d5db")),
        ("TOPPADDING", (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ("LEFTPADDING", (0,0), (-1,-1), 8),
    ]))
    story.append(marks_table)
    story.append(Spacer(1, 0.6*cm))

    # Result summary
    result_color = colors.HexColor("#16a34a") if result_status == "PASS" else colors.HexColor("#dc2626")
    story.append(Paragraph(
        f"<b>Result: <font color='{'#16a34a' if result_status == 'PASS' else '#dc2626'}'>{result_status}</font></b> &nbsp;&nbsp;&nbsp; "
        f"Overall Grade: <b>{overall_grade}</b> &nbsp;&nbsp;&nbsp; "
        f"Percentage: <b>{pct}%</b>",
        ParagraphStyle("result", fontSize=12, spaceAfter=8)
    ))

    story.append(Spacer(1, 1.5*cm))

    # Signatures
    sig_data = [["Class Teacher", "Principal", "Parent/Guardian"]]
    sig_table = Table(sig_data, colWidths=[5.5*cm, 5.5*cm, 5.5*cm])
    sig_table.setStyle(TableStyle([
        ("FONTNAME", (0,0), (-1,-1), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 10),
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ("TOPPADDING", (0,0), (-1,-1), 20),
        ("LINEABOVE", (0,0), (-1,-1), 0.5, colors.grey),
    ]))
    story.append(sig_table)

    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph(
        f"Generated on {datetime.now().strftime('%d %B %Y')} · SchoolSaaS",
        ParagraphStyle("footer", fontSize=8, textColor=colors.grey, alignment=1)
    ))

    doc.build(story)
    buf.seek(0)

    student_name = (user.full_name if user else "student").replace(" ", "_")
    filename = f"Marksheet_{student_name}_{exam.name.replace(' ', '_')}.pdf"

    return StreamingResponse(
        buf,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
