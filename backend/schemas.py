from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field, model_validator


class AccountCreate(BaseModel):
    name: str


class AccountResponse(BaseModel):
    id: int
    name: str
    created_at: datetime

    model_config = {"from_attributes": True}


class PartCreate(BaseModel):
    account_id: int
    supplied_id: Optional[str] = None
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    metadata: Optional[dict] = Field(None, validation_alias='metadata')


class PartUpdate(BaseModel):
    supplied_id: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    metadata: Optional[dict] = None


class PartResponse(BaseModel):
    id: int
    account_id: int
    supplied_id: Optional[str]
    name: str
    description: Optional[str]
    category: Optional[str]
    metadata: Optional[dict]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @model_validator(mode='before')
    @classmethod
    def map_metadata(cls, data: Any) -> Any:
        if hasattr(data, '__dict__'):
            return {
                'id': data.id,
                'account_id': data.account_id,
                'supplied_id': data.supplied_id,
                'name': data.name,
                'description': data.description,
                'category': data.category,
                'metadata': data.part_metadata,
                'created_at': data.created_at,
                'updated_at': data.updated_at,
            }
        return data

class PartRevisionCreate(BaseModel):
    part_id: int
    revision_number: int
    supplied_id: Optional[str] = None
    status: Optional[str] = "draft"
    metadata: Optional[dict] = Field(None, validation_alias='metadata')

class PartRevisionUpdate(BaseModel):
    revision_number: Optional[int] = None
    supplied_id: Optional[str] = None
    status: Optional[str] = None
    metadata: Optional[dict] = None

class PartRevisionResponse(BaseModel):
    id: int
    part_id: int
    revision_number: int
    supplied_id: Optional[str]
    status: str
    metadata: Optional[dict]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @model_validator(mode='before')
    @classmethod
    def map_metadata(cls, data: Any) -> Any:
        if hasattr(data, '__dict__'):
            return {
                'id': data.id,
                'part_id': data.part_id,
                'revision_number': data.revision_number,
                'supplied_id': data.supplied_id,
                'status': data.status,
                'metadata': data.part_metadata,
                'created_at': data.created_at,
                'updated_at': data.updated_at,
            }
        return data

class FileResponse(BaseModel):
    id: int
    part_revision_id: int
    original_filename: str
    file_size: int
    status: str

    model_config = {"from_attributes": True}

class ConversionJobCreate(BaseModel):
    file_id: str
    quality: str

class ConversionJobResponse(BaseModel):
    job_id: str
    status: str

class GeometryCreate(BaseModel):
    part_revision_id: int
    format: str
    version: str
    vertex_count: Optional[int] = None
    face_count: Optional[int] = None
    bounding_box: Optional[dict] = None
    data: Optional[Any] = None

class GeometryResponse(BaseModel):
    id: int
    part_revision_id: int
    format: str
    version: str
    vertex_count: Optional[int] = None
    face_count: Optional[int] = None
    bounding_box: Optional[dict] = None
    created_at: datetime

    model_config = {"from_attributes": True}

class SceneCreate(BaseModel):
    account_id: int
    name: str

class SceneUpdate(BaseModel):
    name: Optional[str] = None
    state: Optional[str] = None

class SceneResponse(BaseModel):
    id: int
    account_id: int
    name: str
    state: str
    created_at: datetime

    model_config = {"from_attributes": True}

class SceneItemCreate(BaseModel):
    part_revision_id: int
    transform_matrix: Optional[dict] = None
    visibility: Optional[bool] = True

class SceneItemResponse(BaseModel):
    id: int
    scene_id: int
    part_revision_id: int
    transform_matrix: Optional[dict] = None
    visibility: bool

    model_config = {"from_attributes": True}
