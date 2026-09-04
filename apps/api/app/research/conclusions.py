from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.models import AnalystConclusion, ResearchCase, ResearchInference, User


OUTCOMES = frozenset(
    {"supported", "partially_supported", "not_supported", "needs_more_research"}
)


class AnalystConclusionService:
    """Persist human judgment without mutating source claims or DealSage inference."""

    def __init__(self, db: Session):
        self.db = db

    def add(
        self,
        case_id: int,
        *,
        analyst_name: str,
        outcome: str,
        statement: str,
        supporting_inference_ids: list[int] | None = None,
        user_id: int | None = None,
        status: str = "draft",
    ) -> AnalystConclusion:
        if self.db.get(ResearchCase, case_id) is None:
            raise ValueError("Research case does not exist")
        if outcome not in OUTCOMES or status not in {"draft", "final"}:
            raise ValueError("Unsupported analyst conclusion outcome or status")
        if not analyst_name.strip() or not statement.strip():
            raise ValueError("Analyst conclusions require an author and statement")
        if user_id is not None and self.db.get(User, user_id) is None:
            raise ValueError("Analyst conclusion user does not exist")
        ids = list(dict.fromkeys(supporting_inference_ids or []))
        inferences = self.db.scalars(
            select(ResearchInference).where(ResearchInference.id.in_(ids))
        ).all()
        if len(inferences) != len(ids) or any(item.case_id != case_id for item in inferences):
            raise ValueError("Conclusion inferences must belong to the same research case")
        conclusion = AnalystConclusion(
            case_id=case_id,
            user_id=user_id,
            analyst_name=analyst_name.strip(),
            outcome=outcome,
            statement=statement.strip(),
            supporting_inference_ids=ids,
            status=status,
        )
        self.db.add(conclusion)
        self.db.commit()
        self.db.refresh(conclusion)
        return conclusion
