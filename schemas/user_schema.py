from schemas.imports import *
from pydantic import Field
import time
from security.hash import hash_password
from typing import List, Optional
from pydantic import BaseModel, EmailStr, model_validator



class UserBase(BaseModel):
    # Shared fields
    admin_approved:Optional[bool]=False
    full_name: str
    email: EmailStr
    password: str | bytes
    role: UserRolesBase
    phone_number: str
    certificate_url: List[str]
    video_url: str
    personality_url: str

    # Client fields
    company_name: Optional[str] = None
    company_email: Optional[str] = None
    company_address: Optional[str] = None
    
    services: Optional[List[Skills]] = None
    client_reason_for_signing_up: Optional[ClientReasonForSignUp] = None
    client_need_agent_work_hours_to_be: Optional[ClientNeedAgentWorkHoursToBe] = None

    # Agent fields
    primary_area_of_expertise: Optional[Skills] = None
    years_of_experience: Optional[int] = None
    three_most_commonly_used_tools_or_platforms: Optional[List[str]] = None
    available_hours_agent_can_commit: Optional[AvailableHoursAgentCanCommit] = None
    time_zone: Optional[UTCOffsets] = None
    portfolio_link: Optional[str] = None
    is_agent_open_to_calls_and_video_meetings: Optional[bool] = None
    does_agent_have_working_computer: Optional[bool] = None
    does_agent_have_stable_internet: Optional[bool] = None
    is_agent_comfortable_with_time_tracking_tools: Optional[bool] = None

    @model_validator(mode='after')
    def validate_role_data(self):
        # --- Validation for client ---
        if self.role == UserRolesBase.client:
            client_required_fields = [
                'company_name',
                'company_email',
                'company_address',
                'full_name',
                'client_reason_for_signing_up',
                'client_need_agent_work_hours_to_be',
                'certificate_url',
                'video_url',
                'personality_url'
            ]

            missing_fields = [
                field_name for field_name in client_required_fields
                if getattr(self, field_name) in [None, [], ""]
            ]
            if missing_fields:
                raise ValueError(
                    f"Missing required fields for client role: {', '.join(missing_fields)}"
                )

        # --- Validation for agent ---
        elif self.role == UserRolesBase.agent:
            agent_required_fields = [
                'primary_area_of_expertise',
                'years_of_experience',
                'three_most_commonly_used_tools_or_platforms',
                'available_hours_agent_can_commit',
                'time_zone',
                'full_name',
                'portfolio_link',
                'is_agent_open_to_calls_and_video_meetings',
                'does_agent_have_working_computer',
                'does_agent_have_stable_internet',
                'is_agent_comfortable_with_time_tracking_tools',
                'certificate_url',
                'video_url',
                'personality_url'
            ]

            missing_fields = [
                field_name for field_name in agent_required_fields
                if getattr(self, field_name) in [None, [], ""]
            ]
            if missing_fields:
                raise ValueError(
                    f"Missing required fields for agent role: {', '.join(missing_fields)}"
                )

        return self


class UserLogin(BaseModel):
    # Add other fields here 
    email:EmailStr
    password:str | bytes
    pass
class UserRefresh(BaseModel):
    # Add other fields here 
    refresh_token:str
    pass


class UserCreate(UserBase):
    # Add other fields here
    role:UserRoles 
    date_created: int = Field(default_factory=lambda: int(time.time()))
    last_updated: int = Field(default_factory=lambda: int(time.time()))
    @model_validator(mode='after')
    def obscure_password(self):
        self.password=hash_password(self.password)
        return self
class UserUpdate(BaseModel):
    # Add other fields here
    admin_approved:Optional[bool]=None 
    password:Optional[str | bytes]=None
    last_updated: int = Field(default_factory=lambda: int(time.time()))
    @model_validator(mode='after')
    def obscure_password(self):
        if self.password:
            self.password=hash_password(self.password)
            return self
class UserOut(UserBase):
    # Add other fields here 
    id: Optional[str] =None
    role:dict
    date_created: Optional[int] = None
    last_updated: Optional[int] = None
    refresh_token: Optional[str] =None
    access_token:Optional[str]=None
    @model_validator(mode='before')
    def set_dynamic_values(cls,values):
        if isinstance(values,dict):
            values['id']= str(values.get('_id'))
            return values
      
            
    class Config:
        from_attributes = True
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str
        }