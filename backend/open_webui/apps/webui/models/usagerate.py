from pydantic import BaseModel, ConfigDict
from typing import Union, Optional

import uuid
from datetime import datetime, timezone, timedelta

from sqlalchemy import String, Column, BigInteger, Text

# from open_webui.utils.misc import get_gravatar_url

from open_webui.apps.webui.internal.db import Base, engine, JSONField, Session, get_db

####################
# UsageRate DB Schema
####################


class UsageRate(Base):
    __tablename__ = "usagerate"
    
    id = Column(String, primary_key=True)
    user_name = Column(String)
    user_id = Column(String)
    user_department = Column(String)
    called_model_name = Column(String)
    called_model_version = Column(String)
    called_time = Column(String)
    user_prompt = Column(String)
    model_ans = Column(String)


class UsageRateModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    user_name : str
    user_id : str
    user_department: str
    called_model_name : str
    called_model_version: str
    called_time : str
    user_prompt : str
    model_ans : str
    
class UsageRateForm(BaseModel):
    
    called_model_name : str
    called_model_version: str
    user_prompt : str
    model_ans : str
    
class ReturnUsageRateModel(BaseModel):
    id : str
    user_name : str
    user_id : str
    user_department: str
    called_model_name : str
    called_model_version: str
    called_time : str
    user_prompt : str
    model_ans : str


class UsageRateTable:
    def save_usagerate(self, user_id: str, user_name:str, user_department:str, form_data:UsageRateForm) -> Optional[ReturnUsageRateModel]:
        try:
            usage_id = str(uuid.uuid4())
            
            now = datetime.now(timezone.utc)
            taiwan_offset = timedelta(hours=8)
            now = now + taiwan_offset
            formatted_date_time = now.strftime("%Y%m%d%H%M")
            with get_db() as db:
                usagerate = ReturnUsageRateModel(
                    **{
                        "id": usage_id,
                        "user_name": user_name,
                        "user_id": user_id,
                        "user_department": user_department,
                        "called_model_name": form_data.called_model_name,
                        "called_model_version": form_data.called_model_version,
                        "called_time": formatted_date_time,
                        "user_prompt": form_data.user_prompt,
                        "model_ans": form_data.model_ans
                    }
                )
                result = UsageRate(**usagerate.model_dump())
                db.add(result)
                db.commit()
                # 紀錄哪個使用者什麼時間 儲存了對話
                print (f"\33[32msave_usagerate: \33[0m\33[1;34m{user_name}\33[0m, Time = {formatted_date_time}")
                db.refresh(result)
                return True
        except Exception as e:
            print(e)
            return False
        
UsageRates = UsageRateTable()