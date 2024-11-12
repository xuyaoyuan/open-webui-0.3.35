from pydantic import BaseModel, ConfigDict
from typing import Union, Optional

import json
import uuid
import time
from datetime import datetime, timezone, timedelta

from sqlalchemy import Column, String, BigInteger, Boolean, Text

from open_webui.apps.webui.internal.db import Base, get_db

####################
# Response DB Schema
####################


class Response(Base):
    __tablename__ = "response"
    
    response_id = Column(String, primary_key=True)
    chat_id = Column(String)
    message_id = Column(String)
    user_id = Column(String)
    used_model = Column(String)
    
    
    feedback = Column(String)
    
    userprompt = Column(String)
    model_ans = Column(String)
    userselectreason = Column(String)
    usercomment = Column(String)
    question_day = Column(String)
    
class ResponseModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    response_id: Optional[str]
    chat_id: str
    message_id: str
    user_id: str
    used_model: Optional[str]
    feedback: str
    userprompt: str
    model_ans:str
    userselectreason: str
    usercomment: str
    question_day: Optional[str]

####################
# Return to DB
####################
class ReturnResponseModel(BaseModel):
    response_id :str
    chat_id: str
    message_id: str
    user_id: str
    used_model: Optional[str]
    feedback: str
    userprompt: str
    model_ans:str
    userselectreason: str
    usercomment: str
    question_day: Optional[str]
    
    
####################
# Forms
#################### 
class ResponseForm(BaseModel):
    chat_id: str
    message_id: str
    used_model: str
    feedback: str
    userprompt: str
    model_ans:str
    userselectreason: str
    usercomment: str
    
class CheckForm(BaseModel):
    message_id :str
    

    
    
class ResponseTable:
    def get_responses(self, skip: int = 0, limit: int = 50) -> list[ResponseModel]:
        try:
            with get_db() as db:
                responses = (
                    db.query(Response)
                    # .offset(skip).limit(limit)
                    .all()
                )
                print(f"Total records found: {len(responses)}")
                return [ResponseModel.model_validate(response) for response in responses]
        except Exception as e:
            print(e)
            return None
        
    def save_response(self, user_id: str, form_data:ResponseForm) -> Optional[ReturnResponseModel]:
        try:
            #獲得response的uuid
            response_id = str(uuid.uuid4())
            #獲得當前日期+小時+分鐘，然後寫入資料庫
            now = datetime.now(timezone.utc)
            taiwan_offset = timedelta(hours=8)
            now = now + taiwan_offset
            formatted_date_time = now.strftime("%Y%m%d%H%M")
            
            with get_db() as db:
                response = ReturnResponseModel(
                    **{
                        "response_id": response_id,
                        "chat_id": form_data.chat_id,
                        "message_id":form_data.message_id,
                        "user_id": user_id,
                        "used_model": form_data.used_model,
                        "feedback": form_data.feedback,
                        "userprompt": form_data.userprompt,
                        "model_ans": form_data.model_ans,
                        "userselectreason":form_data.userselectreason,
                        "usercomment": form_data.usercomment,
                        "question_day": formatted_date_time
                    }
                )
                result = Response(**response.model_dump())
                db.add(result)
                db.commit()
                db.refresh(result)
                return True
        except Exception as e:
            print(e)
            return False
        
    def delete_response_record_by_id(self, response_id: str) -> bool:
        try:
            with get_db() as db:
                # Delete User
                db.query(Response).filter_by(response_id=response_id).delete()
                db.commit()

            return True
        
        except Exception as e:
            print(e)
            return False
    
    def delete_reupdate_response_by_messageId(self, message_id: str) -> bool:
        try:
            with get_db() as db:
                db.query(Response).filter_by(message_id=message_id).delete()
                db.commit()
            return True

        except Exception as e:
            print(e)
            return False
    
    def check_last_message_response_status_by_messageId(self, form_data: CheckForm) -> bool:
        try:
            with get_db() as db:
                res = db.query(Response).filter_by(message_id=form_data).first()
                if (res):
                    return True
                else:
                    return False
        except Exception as e:
            print(e)
            return False
        
Responses = ResponseTable()