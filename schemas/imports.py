from bson import ObjectId
from typing_extensions import Self
from pydantic import GetJsonSchemaHandler
from pydantic import BaseModel, EmailStr, Field,model_validator
from pydantic_core import core_schema
from datetime import datetime,timezone,timedelta
from typing import Optional,List,Any
from enum import Enum
import time
