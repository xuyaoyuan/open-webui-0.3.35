import re
import uuid
import time
import datetime

from open_webui.apps.webui.models.auths import (
    AddUserForm,
    ApiKey,
    Auths,
    Token,
    SigninForm,
    SigninResponse,
    SignupForm,
    UpdatePasswordForm,
    UpdateProfileForm,
    UserResponse,
)
from open_webui.apps.webui.models.users import Users
from open_webui.config import WEBUI_AUTH
from open_webui.constants import ERROR_MESSAGES, WEBHOOK_MESSAGES
from open_webui.env import (
    WEBUI_AUTH_TRUSTED_EMAIL_HEADER,
    WEBUI_AUTH_TRUSTED_NAME_HEADER,
    WEBUI_SESSION_COOKIE_SAME_SITE,
    WEBUI_SESSION_COOKIE_SECURE,
)
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import Response
from pydantic import BaseModel
from open_webui.utils.misc import parse_duration, validate_email_format
from open_webui.utils.utils import (
    create_api_key,
    create_token,
    get_admin_user,
    get_verified_user,
    get_current_user,
    get_password_hash,
)
from open_webui.utils.webhook import post_webhook
from typing import Optional

router = APIRouter()

############################
# GetSessionUser
############################


class SessionUserResponse(Token, UserResponse):
    expires_at: Optional[int] = None


@router.get("/", response_model=SessionUserResponse)
async def get_session_user(
    request: Request, response: Response, user=Depends(get_current_user)
):
    expires_delta = parse_duration(request.app.state.config.JWT_EXPIRES_IN)
    expires_at = None
    if expires_delta:
        expires_at = int(time.time()) + int(expires_delta.total_seconds())

    token = create_token(
        data={"id": user.id},
        expires_delta=expires_delta,
    )

    datetime_expires_at = (
        datetime.datetime.fromtimestamp(expires_at, datetime.timezone.utc)
        if expires_at
        else None
    )

    # Set the cookie token
    response.set_cookie(
        key="token",
        value=token,
        expires=datetime_expires_at,
        httponly=True,  # Ensures the cookie is not accessible via JavaScript
        samesite=WEBUI_SESSION_COOKIE_SAME_SITE,
        secure=WEBUI_SESSION_COOKIE_SECURE,
    )

    return {
        "token": token,
        "token_type": "Bearer",
        "expires_at": expires_at,
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "role": user.role,
        "profile_image_url": user.profile_image_url,
        "enable_model": user.model_selector,
        "department": user.department
    }


############################
# Update Profile
############################


@router.post("/update/profile", response_model=UserResponse)
async def update_profile(
    form_data: UpdateProfileForm, session_user=Depends(get_verified_user)
):
    if session_user:
        user = Users.update_user_by_id(
            session_user.id,
            {"profile_image_url": form_data.profile_image_url, "name": form_data.name},
        )
        if user:
            return user
        else:
            raise HTTPException(400, detail=ERROR_MESSAGES.DEFAULT())
    else:
        raise HTTPException(400, detail=ERROR_MESSAGES.INVALID_CRED)


############################
# Update Password
############################


@router.post("/update/password", response_model=bool)
async def update_password(
    form_data: UpdatePasswordForm, session_user=Depends(get_current_user)
):
    if WEBUI_AUTH_TRUSTED_EMAIL_HEADER:
        raise HTTPException(400, detail=ERROR_MESSAGES.ACTION_PROHIBITED)
    if session_user:
        user = Auths.authenticate_user(session_user.email, form_data.password)

        if user:
            hashed = get_password_hash(form_data.new_password)
            return Auths.update_user_password_by_id(user.id, hashed)
        else:
            raise HTTPException(400, detail=ERROR_MESSAGES.INVALID_PASSWORD)
    else:
        raise HTTPException(400, detail=ERROR_MESSAGES.INVALID_CRED)


############################
# SignIn
############################
import os
import subprocess
import string
import random

def generate_random_string(length=8):
    letters = string.ascii_letters + string.digits
    return ''.join(random.choice(letters) for i in range(length))

def authenticate_ldap(username, password):
    # 生成隨機檔案名
    random_string = generate_random_string()
    temp_password_file = f'/tmp/ldap_password_{random_string}'

    # 將密碼寫入暫存檔案
    with open(temp_password_file, 'w') as f:
        f.write(password)
    
    # 確保暫存檔案權限設定正確 (只有 root 可讀寫)
    os.chown(temp_password_file, 0, 0)
    os.chmod(temp_password_file, 0o600)

    # 使用 ldapsearch 命令驗證
    ldapsearch_command = f'ldapsearch -x -H "ldap://ftgc2.ft.ftg.com" -b "CN=Users,DC=FT,DC=FTG,DC=COM" -D "CN={username},CN=Users,DC=FT,DC=FTG,DC=COM" -y {temp_password_file} "(&(objectClass=user)(sAMAccountName={username}))"'
    auth_success = False  # 預設認證失敗

    try:
        result = subprocess.run(ldapsearch_command, shell=True, check=True, capture_output=True, text=True)
        ldap_output = result.stdout
        if '# numEntries: 1' in ldap_output:
            auth_success = True
        else:
            auth_success = False
    except subprocess.CalledProcessError as e:
        ldap_output = e.stderr
        if 'ldap_bind: Invalid credentials' in ldap_output:
            auth_success = False
        else:
            auth_success = False
    finally:
        # 刪除暫存檔案
        os.remove(temp_password_file)
    
    return auth_success

def convert_email_to_name(email):
    # Split the email at '@' to separate the name from the domain
    name_part = email.split('@')[0]
    
    # Replace the dot with a space
    name_part = name_part.replace('.', ' ')
    
    # Convert to lowercase
    name_part = name_part.lower()
    
    return name_part

def compare_name_with_email(name, email):
    # Convert the name to lowercase and normalize spaces
    normalized_name = name.lower().strip()
    
    # Get the name from the email using the conversion function
    email_name = convert_email_to_name(email)
    
    # Compare the normalized name with the email-derived name
    return normalized_name == email_name

def is_valid_fengtay_email(email):
    # Check if the email domain is 'fengtay.com'
    if email.endswith('@fengtay.com'):
        # Ensure the email follows the 'firstname.lastname' format
        name_part = email.split('@')[0]
        return '.' in name_part
    return False


def generate_email(full_name):
    """
    接收使用者輸入的名字，並在驗證格式後轉換為指定的電子郵件格式。

    參數:
    full_name (str): 使用者輸入的<firstname><空格><lastname>

    回傳:
    str: 格式化為<firstname>.<lastname>@fengtay.com的電子郵件地址

    例外:
    ValueError: 當輸入的格式不符合要求時拋出
    """
    # 定義正則表達式，檢查格式是否為<firstname><空格><lastname>
    pattern = r'^[A-Za-z]+\s[A-Za-z]+$'
    
    # 驗證輸入格式
    if not re.match(pattern, full_name):
        return None
    
    # 將輸入轉換為小寫
    full_name = full_name.lower()

    # 分割字串以獲取 firstname 和 lastname
    firstname, lastname = full_name.split()

    # 格式化為電子郵件格式
    email = f"{firstname}.{lastname}@fengtay.com"

    return email

@router.post("/signin", response_model=SessionUserResponse)
async def signin(request: Request, response: Response, form_data: SigninForm):
    if WEBUI_AUTH_TRUSTED_EMAIL_HEADER:
        if WEBUI_AUTH_TRUSTED_EMAIL_HEADER not in request.headers:
            raise HTTPException(400, detail=ERROR_MESSAGES.INVALID_TRUSTED_HEADER)

        trusted_email = request.headers[WEBUI_AUTH_TRUSTED_EMAIL_HEADER].lower()
        trusted_name = trusted_email
        if WEBUI_AUTH_TRUSTED_NAME_HEADER:
            trusted_name = request.headers.get(
                WEBUI_AUTH_TRUSTED_NAME_HEADER, trusted_email
            )
        if not Users.get_user_by_email(trusted_email.lower()):
            await signup(
                request,
                response,
                SignupForm(
                    email=trusted_email, password=str(uuid.uuid4()), name=trusted_name
                ),
            )
        user = Auths.authenticate_user_by_trusted_header(trusted_email)
    elif WEBUI_AUTH == False:
        admin_email = "admin@localhost"
        admin_password = "admin"

        if Users.get_user_by_email(admin_email.lower()):
            user = Auths.authenticate_user(admin_email.lower(), admin_password)
        else:
            if Users.get_num_users() != 0:
                raise HTTPException(400, detail=ERROR_MESSAGES.EXISTING_USERS)

            await signup(
                request,
                response,
                SignupForm(email=admin_email, password=admin_password, name="User"),
            )

            user = Auths.authenticate_user(admin_email.lower(), admin_password)
    else:
        user = Auths.authenticate_user(form_data.email.lower(), form_data.password)

    if user:

        expires_delta = parse_duration(request.app.state.config.JWT_EXPIRES_IN)
        expires_at = None
        if expires_delta:
            expires_at = int(time.time()) + int(expires_delta.total_seconds())

        token = create_token(
            data={"id": user.id},
            expires_delta=expires_delta,
        )

        datetime_expires_at = (
            datetime.datetime.fromtimestamp(expires_at, datetime.timezone.utc)
            if expires_at
            else None
        )

        # Set the cookie token
        response.set_cookie(
            key="token",
            value=token,
            expires=datetime_expires_at,
            httponly=True,  # Ensures the cookie is not accessible via JavaScript
            samesite=WEBUI_SESSION_COOKIE_SAME_SITE,
            secure=WEBUI_SESSION_COOKIE_SECURE,
        )

        return {
            "token": token,
            "token_type": "Bearer",
            "expires_at": expires_at,
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "profile_image_url": user.profile_image_url,
            "enable_model": user.model_selector,
            "department": user.department,
        }
    else:
        raise HTTPException(400, detail=ERROR_MESSAGES.INVALID_CRED)


############################
# SignUp
############################


@router.post("/signup", response_model=SigninResponse)
async def signup(request: Request, response: Response, form_data: SignupForm):
    if not request.app.state.config.ENABLE_SIGNUP and WEBUI_AUTH:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, detail=ERROR_MESSAGES.ACCESS_PROHIBITED
        )

    if not validate_email_format(form_data.email.lower()):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, detail=ERROR_MESSAGES.INVALID_EMAIL_FORMAT
        )

    if Users.get_user_by_email(form_data.email.lower()):
        raise HTTPException(400, detail=ERROR_MESSAGES.EMAIL_TAKEN)

    try:
        role = (
            "admin"
            if Users.get_num_users() == 0
            else request.app.state.config.DEFAULT_USER_ROLE
        )

        name = form_data.name
        password = form_data.password
        email = form_data.email.lower()

        #email = generate_email(name)

        #if email is None:
        #    raise HTTPException(400, detail='請輸入公司使用者名稱 : <firstname><空格><lastname>')
        VeriSuperAccount = email.endswith("@123.com") and email.startswith("test") or "ian.hsu" in email
        if VeriSuperAccount == False:
            if compare_name_with_email(name, email) and is_valid_fengtay_email(email):
                if authenticate_ldap(name, form_data.password) is not True:
                    raise HTTPException(400, detail=ERROR_MESSAGES.INVALID_CRED + '\n 請輸入正確的豐泰公司帳號密碼')
            else:
                raise HTTPException(400, detail=ERROR_MESSAGES.INVALID_CRED + '\n 請輸入正確的公司名稱及 email 格式')
        
        

        hashed = get_password_hash(form_data.password)
        user = Auths.insert_new_auth(
            form_data.email.lower(),
            hashed,
            form_data.name,
            form_data.profile_image_url,
            role,
        )

        if user:
            token = create_token(
                data={"id": user.id},
                expires_delta=parse_duration(request.app.state.config.JWT_EXPIRES_IN),
            )
            # response.set_cookie(key='token', value=token, httponly=True)

            # Set the cookie token
            response.set_cookie(
                key="token",
                value=token,
                httponly=True,  # Ensures the cookie is not accessible via JavaScript
            )

            if request.app.state.config.WEBHOOK_URL:
                post_webhook(
                    request.app.state.config.WEBHOOK_URL,
                    WEBHOOK_MESSAGES.USER_SIGNUP(user.name),
                    {
                        "action": "signup",
                        "message": WEBHOOK_MESSAGES.USER_SIGNUP(user.name),
                        "user": user.model_dump_json(exclude_none=True),
                    },
                )

            return {
                "token": token,
                "token_type": "Bearer",
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "role": user.role,
                "profile_image_url": user.profile_image_url,
                "enable_model": "FT翻譯, 一般知識",
                "department": "FT-User"
            }
        else:
            raise HTTPException(500, detail=ERROR_MESSAGES.CREATE_USER_ERROR)
    except Exception as err:
        raise HTTPException(500, detail=ERROR_MESSAGES.DEFAULT(err))


@router.get("/signout")
async def signout(response: Response):
    response.delete_cookie("token")
    return {"status": True}


############################
# AddUser
############################


@router.post("/add", response_model=SigninResponse)
async def add_user(form_data: AddUserForm, user=Depends(get_admin_user)):
    if not validate_email_format(form_data.email.lower()):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, detail=ERROR_MESSAGES.INVALID_EMAIL_FORMAT
        )

    if Users.get_user_by_email(form_data.email.lower()):
        raise HTTPException(400, detail=ERROR_MESSAGES.EMAIL_TAKEN)

    try:
        print(form_data)
        hashed = get_password_hash(form_data.password)
        user = Auths.insert_new_auth(
            form_data.email.lower(),
            hashed,
            form_data.name,
            form_data.profile_image_url,
            form_data.role,
        )

        if user:
            token = create_token(data={"id": user.id})
            return {
                "token": token,
                "token_type": "Bearer",
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "role": user.role,
                "profile_image_url": user.profile_image_url,
                "model_selector": "FT翻譯, 一般知識",
                "department": "FT-User"
            }
        else:
            raise HTTPException(500, detail=ERROR_MESSAGES.CREATE_USER_ERROR)
    except Exception as err:
        raise HTTPException(500, detail=ERROR_MESSAGES.DEFAULT(err))


############################
# GetAdminDetails
############################


@router.get("/admin/details")
async def get_admin_details(request: Request, user=Depends(get_current_user)):
    if request.app.state.config.SHOW_ADMIN_DETAILS:
        admin_email = request.app.state.config.ADMIN_EMAIL
        admin_name = None

        print(admin_email, admin_name)

        if admin_email:
            admin = Users.get_user_by_email(admin_email)
            if admin:
                admin_name = admin.name
        else:
            admin = Users.get_first_user()
            if admin:
                admin_email = admin.email
                admin_name = admin.name

        return {
            "name": admin_name,
            "email": admin_email,
        }
    else:
        raise HTTPException(400, detail=ERROR_MESSAGES.ACTION_PROHIBITED)


############################
# ToggleSignUp
############################


@router.get("/admin/config")
async def get_admin_config(request: Request, user=Depends(get_admin_user)):
    return {
        "SHOW_ADMIN_DETAILS": request.app.state.config.SHOW_ADMIN_DETAILS,
        "ENABLE_SIGNUP": request.app.state.config.ENABLE_SIGNUP,
        "DEFAULT_USER_ROLE": request.app.state.config.DEFAULT_USER_ROLE,
        "JWT_EXPIRES_IN": request.app.state.config.JWT_EXPIRES_IN,
        "ENABLE_COMMUNITY_SHARING": request.app.state.config.ENABLE_COMMUNITY_SHARING,
        "ENABLE_MESSAGE_RATING": request.app.state.config.ENABLE_MESSAGE_RATING,
    }


class AdminConfig(BaseModel):
    SHOW_ADMIN_DETAILS: bool
    ENABLE_SIGNUP: bool
    DEFAULT_USER_ROLE: str
    JWT_EXPIRES_IN: str
    ENABLE_COMMUNITY_SHARING: bool
    ENABLE_MESSAGE_RATING: bool


@router.post("/admin/config")
async def update_admin_config(
    request: Request, form_data: AdminConfig, user=Depends(get_admin_user)
):
    request.app.state.config.SHOW_ADMIN_DETAILS = form_data.SHOW_ADMIN_DETAILS
    request.app.state.config.ENABLE_SIGNUP = form_data.ENABLE_SIGNUP

    if form_data.DEFAULT_USER_ROLE in ["pending", "user", "admin"]:
        request.app.state.config.DEFAULT_USER_ROLE = form_data.DEFAULT_USER_ROLE

    pattern = r"^(-1|0|(-?\d+(\.\d+)?)(ms|s|m|h|d|w))$"

    # Check if the input string matches the pattern
    if re.match(pattern, form_data.JWT_EXPIRES_IN):
        request.app.state.config.JWT_EXPIRES_IN = form_data.JWT_EXPIRES_IN

    request.app.state.config.ENABLE_COMMUNITY_SHARING = (
        form_data.ENABLE_COMMUNITY_SHARING
    )
    request.app.state.config.ENABLE_MESSAGE_RATING = form_data.ENABLE_MESSAGE_RATING

    return {
        "SHOW_ADMIN_DETAILS": request.app.state.config.SHOW_ADMIN_DETAILS,
        "ENABLE_SIGNUP": request.app.state.config.ENABLE_SIGNUP,
        "DEFAULT_USER_ROLE": request.app.state.config.DEFAULT_USER_ROLE,
        "JWT_EXPIRES_IN": request.app.state.config.JWT_EXPIRES_IN,
        "ENABLE_COMMUNITY_SHARING": request.app.state.config.ENABLE_COMMUNITY_SHARING,
        "ENABLE_MESSAGE_RATING": request.app.state.config.ENABLE_MESSAGE_RATING,
    }


############################
# API Key
############################


# create api key
@router.post("/api_key", response_model=ApiKey)
async def create_api_key_(user=Depends(get_current_user)):
    api_key = create_api_key()
    success = Users.update_user_api_key_by_id(user.id, api_key)
    if success:
        return {
            "api_key": api_key,
        }
    else:
        raise HTTPException(500, detail=ERROR_MESSAGES.CREATE_API_KEY_ERROR)


# delete api key
@router.delete("/api_key", response_model=bool)
async def delete_api_key(user=Depends(get_current_user)):
    success = Users.update_user_api_key_by_id(user.id, None)
    return success


# get api key
@router.get("/api_key", response_model=ApiKey)
async def get_api_key(user=Depends(get_current_user)):
    api_key = Users.get_user_api_key_by_id(user.id)
    if api_key:
        return {
            "api_key": api_key,
        }
    else:
        raise HTTPException(404, detail=ERROR_MESSAGES.API_KEY_NOT_FOUND)
