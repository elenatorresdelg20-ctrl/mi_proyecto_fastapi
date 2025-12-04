from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from app.schemas.user import UserOut
from app.core.security import authenticate_user, create_access_token, get_current_user

router = APIRouter()

@router.post("/auth/token", response_model=dict)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    token = create_access_token(user.id)
    return {"access_token": token, "token_type": "bearer"}

@router.get("/auth/me", response_model=UserOut)
def read_users_me(current_user = Depends(get_current_user)):
    return current_user
