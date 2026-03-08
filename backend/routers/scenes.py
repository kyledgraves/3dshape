from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from typing import List, Optional

from backend.database import get_db
from backend.models import Scene, SceneItem, Account, PartRevision
from backend.schemas import (
    SceneCreate, SceneUpdate, SceneResponse,
    SceneItemCreate, SceneItemResponse
)

router = APIRouter(tags=["Scenes"])

# Minimal 1x1 JPEG byte array
DUMMY_JPEG = b'\xff\xd8\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xdb\x00C\x01\t\t\t\x0c\x0b\x0c\x18\r\r\x182!\x1c!22222222222222222222222222222222222222222222222222\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xc4\x00\xb5\x10\x00\x02\x01\x03\x03\x02\x04\x03\x05\x05\x04\x04\x00\x00\x01}\x01\x02\x03\x00\x04\x11\x05\x12!1A\x06\x13Qa\x07"q\x142\x81\x91\xa1\x08#B\xb1\xc1\x15R\xd1\xf0$3br\x82\t\n\x16\x17\x18\x19\x1a%&\'()*456789:CDEFGHIJSTUVWXYZcdefghijstuvwxyz\x83\x84\x85\x86\x87\x88\x89\x8a\x92\x93\x94\x95\x96\x97\x98\x99\x9a\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xe1\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xf1\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xff\xc4\x00\x1f\x01\x00\x03\x01\x01\x01\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xc4\x00\xb5\x11\x00\x02\x01\x02\x04\x04\x03\x04\x07\x05\x04\x04\x00\x01\x02w\x00\x01\x02\x03\x11\x04\x05!1\x06\x12AQ\x07aq\x13"2\x81\x08\x14B\x91\xa1\xb1\xc1\t#3R\xf0\x15br\xd1\n\x16$4\xe1%\xf1\x17\x18\x19\x1a&\'()*56789:CDEFGHIJSTUVWXYZcdefghijstuvwxyz\x82\x83\x84\x85\x86\x87\x88\x89\x8a\x92\x93\x94\x95\x96\x97\x98\x99\x9a\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00?\x00\xfd\xfc\x9b\xa9\xff\xd9'

@router.post("/scenes", response_model=SceneResponse, status_code=201)
def create_scene(scene: SceneCreate, db: Session = Depends(get_db)):
    db_account = db.query(Account).filter(Account.id == scene.account_id).first()
    if not db_account:
        raise HTTPException(status_code=404, detail="Account not found")
        
    db_scene = Scene(
        account_id=scene.account_id,
        name=scene.name,
        state="draft"
    )
    db.add(db_scene)
    db.commit()
    db.refresh(db_scene)
    return db_scene

@router.get("/scenes", response_model=List[SceneResponse])
def list_scenes(account_id: Optional[int] = None, db: Session = Depends(get_db)):
    query = db.query(Scene)
    if account_id is not None:
        query = query.filter(Scene.account_id == account_id)
    return query.all()

@router.get("/scenes/{id}", response_model=SceneResponse)
def get_scene(id: int, db: Session = Depends(get_db)):
    db_scene = db.query(Scene).filter(Scene.id == id).first()
    if not db_scene:
        raise HTTPException(status_code=404, detail="Scene not found")
    return db_scene

@router.get("/scenes/{id}/image", response_class=Response)
def render_scene_image(id: int, width: int = 1920, height: int = 1080, db: Session = Depends(get_db)):
    db_scene = db.query(Scene).filter(Scene.id == id).first()
    if not db_scene:
        raise HTTPException(status_code=404, detail="Scene not found")
    return Response(content=DUMMY_JPEG, media_type="image/jpeg")

@router.patch("/scenes/{id}", response_model=SceneResponse)
def update_scene(id: int, scene_update: SceneUpdate, db: Session = Depends(get_db)):
    db_scene = db.query(Scene).filter(Scene.id == id).first()
    if not db_scene:
        raise HTTPException(status_code=404, detail="Scene not found")
        
    update_data = scene_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_scene, key, value)
        
    db.commit()
    db.refresh(db_scene)
    return db_scene

@router.delete("/scenes/{id}", status_code=204)
def delete_scene(id: int, db: Session = Depends(get_db)):
    db_scene = db.query(Scene).filter(Scene.id == id).first()
    if not db_scene:
        raise HTTPException(status_code=404, detail="Scene not found")
    
    db.delete(db_scene)
    db.commit()
    return None

@router.post("/scenes/{id}/items", response_model=SceneItemResponse, status_code=201)
def create_scene_item(id: int, item: SceneItemCreate, db: Session = Depends(get_db)):
    db_scene = db.query(Scene).filter(Scene.id == id).first()
    if not db_scene:
        raise HTTPException(status_code=404, detail="Scene not found")
        
    db_part_rev = db.query(PartRevision).filter(PartRevision.id == item.part_revision_id).first()
    if not db_part_rev:
        raise HTTPException(status_code=404, detail="Part revision not found")
        
    db_item = SceneItem(
        scene_id=id,
        part_revision_id=item.part_revision_id,
        transform_matrix=item.transform_matrix or {},
        visibility=item.visibility if item.visibility is not None else True
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@router.get("/scenes/{id}/items", response_model=List[SceneItemResponse])
def list_scene_items(id: int, db: Session = Depends(get_db)):
    db_scene = db.query(Scene).filter(Scene.id == id).first()
    if not db_scene:
        raise HTTPException(status_code=404, detail="Scene not found")
        
    return db.query(SceneItem).filter(SceneItem.scene_id == id).all()

@router.delete("/scenes/{id}/items/{item_id}", status_code=204)
def delete_scene_item(id: int, item_id: int, db: Session = Depends(get_db)):
    db_item = db.query(SceneItem).filter(SceneItem.scene_id == id, SceneItem.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Scene item not found")
        
    db.delete(db_item)
    db.commit()
    return None
