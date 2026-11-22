from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user, get_profile
from ..ml.nutrition import compute_targets
from ..models import User
from ..schemas import ProfileIn, ProfileOut

router = APIRouter(prefix="/api/profile", tags=["profile"])


def _payload(profile):
    return {"profile": ProfileOut.model_validate(profile), "targets": compute_targets(profile)}


@router.get("")
def read_profile(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return _payload(get_profile(db, user))


@router.put("")
def update_profile(data: ProfileIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    profile = get_profile(db, user)
    for k, v in data.model_dump().items():
        setattr(profile, k, [a.strip().lower() for a in v if a.strip()] if k == "allergies" else v)
    db.commit()
    return _payload(profile)
