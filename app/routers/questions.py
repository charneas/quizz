from fastapi import APIRouter, HTTPException, Depends, Query, Request, Response
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
from typing import List
from datetime import datetime
from app.db import get_session
from app.models import PendingQuestion, Question, Admin
from app.auth import get_admin
from pydantic import BaseModel, EmailStr

def add_security_headers(response: Response):
    """Ajoute les en-têtes de sécurité pour forcer l'authentification"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"

templates = Jinja2Templates(directory="app/templates")

router = APIRouter(prefix="/questions", tags=["questions"])

class QuestionSubmission(BaseModel):
    text: str
    answer: str
    theme: str
    difficulty: str  # Facile, Moyen, Difficile
    submitter_name: str
    submitter_email: EmailStr

class AdminReview(BaseModel):
    action: str  # "approve" ou "reject"
    comment: str = None

@router.get("/themes")
async def get_themes(session: Session = Depends(get_session)):
    """Récupérer la liste des thèmes existants"""
    statement = select(Question.theme).distinct()
    themes = session.exec(statement).all()
    return sorted(themes)

@router.post("/submit")
async def submit_question(
    submission: QuestionSubmission,
    session: Session = Depends(get_session)
):
    """Soumettre une nouvelle question pour validation"""
    # Convertir la difficulté en nombre
    difficulty_map = {
        'Facile': 1,
        'Moyen': 2,
        'Difficile': 3
    }
    
    if submission.difficulty not in difficulty_map:
        raise HTTPException(
            status_code=400,
            detail="La difficulté doit être 'Facile', 'Moyen' ou 'Difficile'"
        )
    
    # Créer la question en attente
    pending_question = PendingQuestion(
        text=submission.text,
        answer=submission.answer,
        theme=submission.theme,
        difficulty=difficulty_map[submission.difficulty],
        submitter_name=submission.submitter_name,
        submitter_email=submission.submitter_email
    )
    
    session.add(pending_question)
    session.commit()
    session.refresh(pending_question)
    
    return {"message": "Question soumise avec succès!", "id": pending_question.id}

@router.get("/pending", response_model=List[PendingQuestion])
async def list_pending_questions(
    admin: Admin = Depends(get_admin),
    session: Session = Depends(get_session),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    response: Response = None
):
    """Liste les questions en attente de validation (admin seulement)"""
    add_security_headers(response)
    statement = select(PendingQuestion).where(
        PendingQuestion.status == "pending"
    ).offset(skip).limit(limit)
    return session.exec(statement).all()

@router.post("/pending/{question_id}/review")
async def review_question(
    question_id: int,
    review: AdminReview,
    admin: Admin = Depends(get_admin),
    session: Session = Depends(get_session),
    response: Response = None
):
    """Approuver ou rejeter une question en attente (admin seulement)"""
    add_security_headers(response)
    # Récupérer la question en attente
    statement = select(PendingQuestion).where(PendingQuestion.id == question_id)
    pending_question = session.exec(statement).first()
    if not pending_question:
        raise HTTPException(status_code=404, detail="Question non trouvée")
    
    if review.action == "approve":
        # Créer une nouvelle question approuvée
        question = Question(
            text=pending_question.text,
            answer=pending_question.answer,
            theme=pending_question.theme,
            difficulty=pending_question.difficulty,
            points=pending_question.points,
            created_by=pending_question.submitter_name
        )
        session.add(question)
        pending_question.status = "approved"
    
    elif review.action == "reject":
        if not review.comment:
            raise HTTPException(
                status_code=400,
                detail="Un commentaire est requis pour rejeter une question"
            )
        pending_question.status = "rejected"
        pending_question.admin_comment = review.comment
    
    else:
        raise HTTPException(
            status_code=400,
            detail="L'action doit être 'approve' ou 'reject'"
        )
    
    session.commit()
    return {"message": f"Question {review.action}d avec succès!"}
