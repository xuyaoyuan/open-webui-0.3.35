from fastapi import Depends, Request, HTTPException, status
from typing import Union, Optional
from open_webui.utils.utils import get_verified_user, get_admin_user
from fastapi import APIRouter
from pydantic import BaseModel
import json
import logging

from open_webui.apps.webui.models.users import Users

from open_webui.apps.webui.models.usagerate import (
    UsageRateModel,
    UsageRateForm,
    UsageRates
)

from open_webui.constants import ERROR_MESSAGES
from open_webui.env import SRC_LOG_LEVELS

log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["MODELS"])

router = APIRouter()


############################
# WriteUserUsageRate
############################

@router.post("/save_usagerate", response_model=bool)
async def save_user_response(form_data: UsageRateForm, user=Depends(get_verified_user)):
    res = UsageRates.save_usagerate(user.id, user.name, user.department, form_data)
    return res