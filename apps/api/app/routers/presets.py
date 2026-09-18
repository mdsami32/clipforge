import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import db, schemas

router = APIRouter(prefix="/presets", tags=["presets"])

# Sensible starting presets for the three launch platforms. Seeded on first
# request if the table is empty — see seed_defaults().
_DEFAULTS = [
    schemas.PresetCreate(
        name="YouTube Shorts",
        platform="youtube",
        resolution_w=1080,
        resolution_h=1920,
        bitrate_kbps=10000,
        safe_zone_margins={"top": 140, "bottom": 220, "left": 40, "right": 40},
        is_default=True,
    ),
    schemas.PresetCreate(
        name="TikTok",
        platform="tiktok",
        resolution_w=1080,
        resolution_h=1920,
        bitrate_kbps=8000,
        safe_zone_margins={"top": 120, "bottom": 260, "left": 40, "right": 160},
        is_default=True,
    ),
    schemas.PresetCreate(
        name="Instagram Reels",
        platform="instagram",
        resolution_w=1080,
        resolution_h=1920,
        bitrate_kbps=8500,
        safe_zone_margins={"top": 120, "bottom": 240, "left": 40, "right": 40},
        is_default=True,
    ),
]


def seed_defaults(session: Session):
    if session.query(db.Preset).count() > 0:
        return
    for p in _DEFAULTS:
        session.add(db.Preset(**p.model_dump()))
    session.commit()


@router.get("", response_model=list[schemas.PresetOut])
def list_presets(session: Session = Depends(db.get_db)):
    seed_defaults(session)
    return session.query(db.Preset).all()


@router.post("", response_model=schemas.PresetOut)
def create_preset(payload: schemas.PresetCreate, session: Session = Depends(db.get_db)):
    preset = db.Preset(**payload.model_dump())
    session.add(preset)
    session.commit()
    session.refresh(preset)
    return preset


@router.patch("/{preset_id}", response_model=schemas.PresetOut)
def update_preset(preset_id: uuid.UUID, payload: schemas.PresetCreate, session: Session = Depends(db.get_db)):
    preset = session.get(db.Preset, preset_id)
    if not preset:
        raise HTTPException(status_code=404, detail="Preset not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(preset, field, value)
    session.commit()
    session.refresh(preset)
    return preset


@router.delete("/{preset_id}", status_code=204)
def delete_preset(preset_id: uuid.UUID, session: Session = Depends(db.get_db)):
    preset = session.get(db.Preset, preset_id)
    if preset:
        session.delete(preset)
        session.commit()
