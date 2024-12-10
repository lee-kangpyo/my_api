from pydantic import BaseModel, ConfigDict
from fastapi import UploadFile
from typing import List

class Suggetion(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    suggestion: str
    additional: str

class Bug(BaseModel):
    # model_config = ConfigDict(from_attributes=True)
    bug: str
    step: str
