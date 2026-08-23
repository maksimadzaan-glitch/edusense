from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class TeacherCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    email: str = Field(..., min_length=5, max_length=200, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class ClassCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    subject: str = Field(..., min_length=2, max_length=80)
    target_exam: str = Field(..., pattern="^(vpr|oge|ege|school)$")
    teacher_id: Optional[int] = None
    teacher: Optional[TeacherCreate] = None


class TeacherOut(BaseModel):
    id: int
    name: str
    email: str

    class Config:
        from_attributes = True


class ClassOut(BaseModel):
    id: int
    teacher_id: int
    name: str
    code: str
    subject: str
    target_exam: str

    class Config:
        from_attributes = True


class ClassCreateResponse(BaseModel):
    classroom: ClassOut
    teacher: TeacherOut


class AiGenerateRequest(BaseModel):
    exam: str = Field(..., min_length=2, max_length=40)
    subject: str = Field(..., min_length=2, max_length=80)
    difficulty: Literal["easy", "medium", "hard"] = "medium"
    count: Optional[int] = Field(None, ge=1, le=50)
    # устарело: /generate всегда PostgreSQL-шаблоны (не SQLite-банк)
    source: Literal["bank", "ai", "hybrid"] = "hybrid"
    prefer_pg: bool = True
    # опциональная лёгкая LLM-вариация чисел/формулировок (по умолчанию выкл.)
    vary: bool = False
    # etalon — только импортированные эталонные варианты (vary игнорируется)
    mode: Optional[Literal["etalon"]] = None
    # тематический фокус: оставить только эти номера слотов КИМ
    slots: Optional[List[int]] = None



class QuestionOut(BaseModel):
    num: int
    part: int
    type: str
    topic: str
    text: str
    answer: str
    max_score: int = 1
    section: Optional[str] = None
    needs_figure: bool = False
    figure_kind: Optional[str] = None
    figure_svg: Optional[str] = None
    # Чертёж к решению (часть 2 геометрия) — только учительский ключ, не ученику
    solution_figure_svg: Optional[str] = None
    # ОГЭ русский и др.: listening / matching / essay_options / shared texts
    payload: Optional[dict[str, Any]] = None
    # Сохранять порядок КИМ (изложение первым), не part1→part2
    kim_order: bool = False
    # альтернативные формы ключа (для автопроверки)
    acceptable_answers: Optional[List[Any]] = None
    # краткий комментарий к ключу (solution_hint) — только учительский API
    solution: Optional[str] = None


class AiGenerateResponse(BaseModel):
    exam: str
    subject: str
    difficulty: str
    questions: List[QuestionOut]
    source: Literal["bank", "ai", "hybrid"] = "hybrid"
    message: Optional[str] = None
    bank_stats: Optional[dict[str, Any]] = None
    # фронт: принудительно включить КИМ-UI ОГЭ русский
    exam_ui: Optional[str] = None
    # честный лейбл «Эталонный вариант» (не «официальный ФИПИ» без лицензии)
    etalon: bool = False
    provenance: Optional[dict[str, Any]] = None
    # ОГЭ русский: «База №1 · Честность» / код Б1
    variant_label: Optional[str] = None
    bank_code: Optional[str] = None
    bank: Optional[dict[str, Any]] = None


class AssignmentPublishRequest(BaseModel):
    class_id: Optional[int] = None
    class_code: Optional[str] = None
    title: str = Field(..., min_length=2, max_length=200)
    deadline: Optional[datetime] = None
    # TZ alias
    deadline_at: Optional[datetime] = None
    timer_minutes: Optional[int] = Field(None, ge=1, le=600)
    # TZ alias
    time_limit_minutes: Optional[int] = Field(None, ge=1, le=600)
    shuffle_variants: bool = True
    difficulty: Optional[Literal["easy", "medium", "hard"]] = None
    questions: List[dict[str, Any]] = Field(..., min_length=1)
    grading_mode: Literal["ai_assist", "manual", "autopilot"] = "ai_assist"
    block_copy: bool = False
    hide_answers: bool = False
    allowed_students: Optional[List[str]] = None


class AssignmentPatchRequest(BaseModel):
    """Частичное обновление работы: дедлайн, приём сдач, статус."""

    deadline: Optional[datetime] = None
    deadline_at: Optional[datetime] = None
    extend_deadline_days: Optional[int] = Field(None, ge=1, le=30)
    timer_minutes: Optional[int] = Field(None, ge=1, le=600)
    time_limit_minutes: Optional[int] = Field(None, ge=1, le=600)
    shuffle_variants: Optional[bool] = None
    accepting_submissions: Optional[bool] = None
    status: Optional[Literal["draft", "active", "closed"]] = None
    expected_students: Optional[int] = Field(None, ge=1, le=500)


class AssignmentOut(BaseModel):
    id: int
    class_id: int
    title: str
    code: str
    deadline: Optional[datetime] = None
    deadline_at: Optional[datetime] = None
    timer_minutes: Optional[int] = None
    time_limit_minutes: Optional[int] = None
    shuffle_variants: bool = False
    accepting_submissions: bool = True
    expected_students: Optional[int] = None
    questions: List[dict[str, Any]]
    question_count: int = 0
    grading_mode: str
    status: str
    class_code: Optional[str] = None
    subject: Optional[str] = None
    target_exam: Optional[str] = None
    student_url: Optional[str] = None
    # опционально на публичном GET (ученик) — не ломает учителя
    etalon: bool = False
    exam_ui: Optional[str] = None
    provenance: Optional[dict[str, Any]] = None
    unique_applied: bool = False
    unique_changed: int = 0
    already_submitted: bool = False
    block_copy: bool = False
    hide_answers: bool = False
    answers_locked: bool = False
    allowed_students: Optional[List[str]] = None

    class Config:
        from_attributes = True


class AssignmentListItem(BaseModel):
    """Карточка работы в списке учителя (без полного JSON вопросов)."""

    id: int
    code: str
    title: str
    subject: Optional[str] = None
    exam: Optional[str] = None
    status: str
    grading_mode: str
    created_at: Optional[datetime] = None
    deadline: Optional[datetime] = None
    deadline_at: Optional[datetime] = None
    timer_minutes: Optional[int] = None
    time_limit_minutes: Optional[int] = None
    shuffle_variants: bool = False
    accepting_submissions: bool = True
    expected_students: Optional[int] = None
    student_url: Optional[str] = None
    student_path: Optional[str] = None
    submissions_count: int = 0
    unique_submitters: int = 0
    questions_count: int = 0
    submissions_today: int = 0


class SubmissionAnswerView(BaseModel):
    """Ответ ученика для просмотра учителем (только чтение)."""

    num: int
    text: str = ""
    has_photo: bool = False
    photo_data_url: Optional[str] = None
    question_text: Optional[str] = None
    topic: Optional[str] = None
    correct_answer: Optional[str] = None
    part: Optional[int] = None
    solution: Optional[str] = None
    max_score: Optional[int] = None
    earned: Optional[float] = None
    status: Optional[str] = None
    comment: Optional[str] = None
    ai_grade: Optional[dict[str, Any]] = None
    source_text: Optional[str] = None
    teacher_override: bool = False


class AnswerKeyItem(BaseModel):
    """Правильный ответ задания для ведомости учителя."""

    num: int
    topic: Optional[str] = None
    answer: str = ""
    max_score: int = 1
    part: int = 1
    solution: Optional[str] = None


class SubmissionListItem(BaseModel):
    """Строка сдачи для таблицы учителя."""

    id: int
    student_name: str
    score: Optional[float] = None
    max_score: Optional[float] = None
    status: str
    submitted_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    review_summary: Optional[str] = None
    teacher_score: Optional[float] = None
    teacher_comment: Optional[str] = None
    teacher_reviewed_at: Optional[datetime] = None
    answers: List[SubmissionAnswerView] = Field(default_factory=list)


class SubmissionGradePatch(BaseModel):
    """Ручная оценка и комментарий учителя по сдаче."""

    teacher_score: Optional[float] = Field(None, ge=0, le=500)
    teacher_comment: Optional[str] = Field(None, max_length=4000)
    status: Optional[Literal["pending", "ai_reviewed", "approved", "graded"]] = None
    item_num: Optional[int] = Field(None, ge=1, le=40)
    item_earned: Optional[float] = Field(None, ge=0, le=20)
    item_comment: Optional[str] = Field(None, max_length=2000)
    ai_grade: Optional[dict[str, Any]] = None


class StudentQuestionOut(BaseModel):
    num: int
    part: int
    type: str
    topic: str
    text: str
    max_score: int = 1
    figure_kind: Optional[str] = None
    figure_svg: Optional[str] = None
    payload: Optional[dict[str, Any]] = None
    kim_order: bool = False


class StudentAssignmentOut(BaseModel):
    id: int
    title: str
    code: str
    deadline: Optional[datetime] = None
    deadline_at: Optional[datetime] = None
    timer_minutes: Optional[int] = None
    time_limit_minutes: Optional[int] = None
    shuffle_variants: bool = False
    accepting_submissions: bool = True
    questions: List[StudentQuestionOut]
    question_count: int = 0
    grading_mode: str
    status: str
    subject: Optional[str] = None
    target_exam: Optional[str] = None
    # эталонный комплект (импорт без AI) — для бейджа у ученика
    etalon: bool = False
    exam_ui: Optional[str] = None
    provenance: Optional[dict[str, Any]] = None
    unique_applied: bool = False
    unique_changed: int = 0
    already_submitted: bool = False
    block_copy: bool = False
    hide_answers: bool = False
    answers_locked: bool = False


class AnswerItemIn(BaseModel):
    num: int
    text: Optional[str] = ""
    photo_data_url: Optional[str] = None


class SubmissionCreateRequest(BaseModel):
    student_name: str = Field(..., min_length=2, max_length=120)
    answers: List[AnswerItemIn] = Field(..., min_length=1)
    started_at: Optional[datetime] = None


class SubmissionOut(BaseModel):
    id: int
    assignment_id: int
    student_name: str
    score: Optional[float] = None
    max_score: Optional[float] = None
    status: str
    answers: dict[str, Any] = Field(default_factory=dict)
    ai_review: Optional[dict[str, Any]] = None
    started_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    teacher_score: Optional[float] = None
    teacher_comment: Optional[str] = None
    teacher_reviewed_at: Optional[datetime] = None
    oge: Optional[dict[str, Any]] = None
    already_submitted: bool = False


class RosterPutRequest(BaseModel):
    names: List[str] = Field(default_factory=list)


class RosterEntryOut(BaseModel):
    id: int
    name: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class RosterOut(BaseModel):
    class_code: str
    names: List[str]
    entries: List[RosterEntryOut] = Field(default_factory=list)
    count: int = 0


class StudentCardOut(BaseModel):
    name: str
    in_roster: bool = True
    avg_score: Optional[float] = None
    avg_percent: Optional[float] = None
    submissions_count: int = 0
    weak_topics: List[str] = Field(default_factory=list)
    last_activity_at: Optional[datetime] = None


class StudentsListOut(BaseModel):
    class_code: str
    roster_count: int = 0
    students: List[StudentCardOut] = Field(default_factory=list)


class AnalyticsAssignmentOption(BaseModel):
    code: str
    title: str
    created_at: Optional[datetime] = None
    submissions_count: int = 0
    avg_percent: Optional[float] = None


class AnalyticsHeatItem(BaseModel):
    num: int
    topic: Optional[str] = None
    wrong_count: int = 0
    empty_count: int = 0
    correct_count: int = 0
    pending_count: int = 0
    total: int = 0
    wrong_pct: float = 0.0
    success_pct: Optional[float] = None
    flag: Optional[str] = None
    wrong_students: List[str] = Field(default_factory=list)
    empty_students: List[str] = Field(default_factory=list)
    typical_wrong: Optional[str] = None
    typical_wrong_count: int = 0
    delta_pct: Optional[float] = None


class AnalyticsTrendPoint(BaseModel):
    assignment_code: str
    title: str
    created_at: Optional[datetime] = None
    avg_percent: Optional[float] = None
    submissions_count: int = 0


class AnalyticsTimeStats(BaseModel):
    avg_duration_seconds: Optional[int] = None
    samples: int = 0
    per_task_available: bool = False


class AnalyticsParticipation(BaseModel):
    roster_count: int = 0
    submitters_count: int = 0
    submissions_count: int = 0
    participation_pct: Optional[float] = None
    expected_students: Optional[int] = None
    all_submitted: bool = False
    missing_students: List[str] = Field(default_factory=list)
    submitted_students: List[str] = Field(default_factory=list)


class AnalyticsMarkBucket(BaseModel):
    mark: int
    count: int = 0


class AnalyticsRiskStudent(BaseModel):
    name: str
    red_count: int = 0
    nums: List[int] = Field(default_factory=list)


class AnalyticsGradeRow(BaseModel):
    name: str
    submitted: bool = False
    primary: Optional[int] = None
    max_primary: int = 31
    grade: Optional[str] = None
    failed_geometry: bool = False
    failed_literacy: bool = False
    geometry_score: Optional[int] = None
    geometry_max: Optional[int] = None
    literacy_score: Optional[int] = None
    weak_topics: List[str] = Field(default_factory=list)
    geometry_tag: Optional[str] = None
    literacy_tag: Optional[str] = None
    part1_score: Optional[int] = None
    part2_score: Optional[int] = None
    threshold_status: Optional[str] = None


class ClassAnalyticsOut(BaseModel):
    class_code: str
    mode: Literal["class", "student"] = "class"
    student: Optional[str] = None
    students: List[str] = Field(default_factory=list)
    assignments: List[AnalyticsAssignmentOption] = Field(default_factory=list)
    selected_assignment_code: Optional[str] = None
    selected_assignment_title: Optional[str] = None
    class_avg_percent: Optional[float] = None
    participation: AnalyticsParticipation = Field(default_factory=AnalyticsParticipation)
    heatmap: List[AnalyticsHeatItem] = Field(default_factory=list)
    weakest_nums: List[int] = Field(default_factory=list)
    flags: List[str] = Field(default_factory=list)
    trend: List[AnalyticsTrendPoint] = Field(default_factory=list)
    time: AnalyticsTimeStats = Field(default_factory=AnalyticsTimeStats)
    summary_lines: List[str] = Field(default_factory=list)
    remediation_ready: bool = False
    remediation_hint: Optional[str] = None
    mark_distribution: List[AnalyticsMarkBucket] = Field(default_factory=list)
    risk_students: List[AnalyticsRiskStudent] = Field(default_factory=list)
    compare_assignment_code: Optional[str] = None
    compare_assignment_title: Optional[str] = None
    subject: Optional[str] = None
    grade_rows: List[AnalyticsGradeRow] = Field(default_factory=list)
    class_avg_primary: Optional[float] = None
    class_avg_grade: Optional[float] = None


class RemediationRequest(BaseModel):
    assignment_code: Optional[str] = None
    student: Optional[str] = None
    max_tasks: int = Field(5, ge=1, le=20)
    grading_mode: Literal["ai_assist", "manual", "autopilot"] = "ai_assist"


class RnoPreviewRequest(BaseModel):
    assignment_code: Optional[str] = None
    student: Optional[str] = None
    max_tasks: int = Field(25, ge=1, le=25)


class RnoPreviewOut(BaseModel):
    title: str
    source_title: Optional[str] = None
    source_assignment_code: Optional[str] = None
    failed_nums: List[int] = Field(default_factory=list)
    questions: List[Dict[str, Any]] = Field(default_factory=list)
    exam_ui: Optional[str] = None
    mutated_count: int = 0
    used_alt: bool = False


# --- Student cabinet (join + dashboard) ---


class StudentJoinRequest(BaseModel):
    code: str = Field(..., min_length=3, max_length=32)
    name: str = Field(..., min_length=2, max_length=120)


class StudentJoinAssignmentOut(BaseModel):
    id: int
    code: str
    title: str
    status: str
    accepting_submissions: bool = True
    questions_count: int = 0
    deadline: Optional[datetime] = None
    deadline_at: Optional[datetime] = None
    timer_minutes: Optional[int] = None
    time_limit_minutes: Optional[int] = None
    subject: Optional[str] = None


class StudentJoinOut(BaseModel):
    student_id: str
    student_name: str
    class_code: str
    class_name: str
    subject: str
    exam: str
    assignment: Optional[StudentJoinAssignmentOut] = None
    join_kind: Literal["class", "assignment"] = "class"


class StudentTaskCardOut(BaseModel):
    id: int
    code: str
    title: str
    subject: Optional[str] = None
    exam: Optional[str] = None
    status: str
    accepting_submissions: bool = True
    questions_count: int = 0
    deadline: Optional[datetime] = None
    deadline_at: Optional[datetime] = None
    timer_minutes: Optional[int] = None
    time_limit_minutes: Optional[int] = None
    badge: Literal["new", "in_progress", "done"] = "new"
    # completed fields
    score: Optional[float] = None
    max_score: Optional[float] = None
    grade: Optional[str] = None
    submitted_at: Optional[datetime] = None
    submission_id: Optional[int] = None
    has_review: bool = False
    review_summary: Optional[str] = None
    ai_review: Optional[dict[str, Any]] = None
    teacher_score: Optional[float] = None
    teacher_comment: Optional[str] = None
    teacher_reviewed_at: Optional[datetime] = None
    oge: Optional[dict[str, Any]] = None
    hide_answers: bool = False
    answers_locked: bool = False


class StudentStatsOut(BaseModel):
    completed_count: int = 0
    avg_accuracy: Optional[float] = None


class StudentLeaderRowOut(BaseModel):
    rank: int = 0
    name: str
    short_name: str
    xp: int = 0
    streak: int = 0
    you: bool = False


class StudentTasksOut(BaseModel):
    class_code: str
    class_name: str = ""
    subject: str = ""
    exam: str = ""
    student_name: str
    active: List[StudentTaskCardOut] = Field(default_factory=list)
    completed: List[StudentTaskCardOut] = Field(default_factory=list)
    stats: StudentStatsOut = Field(default_factory=StudentStatsOut)
    leaderboard: List[StudentLeaderRowOut] = Field(default_factory=list)
