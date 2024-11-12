from fastapi import Depends, Request, HTTPException, status
from typing import Union, Optional
from open_webui.utils.utils import get_verified_user, get_admin_user
from fastapi import APIRouter
from pydantic import BaseModel
import json
import logging

from open_webui.apps.webui.models.users import Users

from open_webui.apps.webui.models.responses import (
    ResponseModel,
    ResponseForm,
    CheckForm,
    Responses
)

from open_webui.constants import ERROR_MESSAGES
from open_webui.env import SRC_LOG_LEVELS

log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["MODELS"])

router = APIRouter()


############################
# Get Responses
############################

@router.get("/", response_model=list[ResponseModel])
async def Get_Responses(skip: int = 0, limit: int = 50, user=Depends(get_admin_user)):
    return Responses.get_responses(skip, limit)



############################
# WriteUserResponse
############################

@router.post("/save_response", response_model=bool)
async def save_user_response(form_data: ResponseForm, user=Depends(get_verified_user)):
    # 先判斷是否以前有存過，如果有就刪除舊的 貼上新的
    Responses.delete_reupdate_response_by_messageId(form_data.message_id)
    res = Responses.save_response(user.name, form_data)
    return res



############################
# DeleteResponseRecord
############################

@router.delete("/{response_id}", response_model=bool)
async def delete_response_by_id(response_id: str, user=Depends(get_admin_user)):
    if user:
        res = Responses.delete_response_record_by_id(response_id)
        
        if res:
            return True
        
        raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=ERROR_MESSAGES.DELETE_RESPONSE_ERROR,
            )
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=ERROR_MESSAGES.ACTION_PROHIBITED,
    )
    
############################
# Check Last Message Response Status
############################

@router.post("/CheckStatus", response_model=bool)
async def check_response_status_by_messageId(form_data: CheckForm, user=Depends(get_verified_user)):
    if (user):
        res = Responses.check_last_message_response_status_by_messageId(form_data.message_id)
        if (res):
            return True
        else:
            return False
        
    raise HTTPException(
        status_code = status.HTTP_403_FORBIDDEN,
        detail=ERROR_MESSAGES.ACTION_PROHIBITED,
    )