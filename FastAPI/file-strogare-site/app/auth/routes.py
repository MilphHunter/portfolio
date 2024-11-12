from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Request, Depends, HTTPException, status, Form, Response
from jose import jwt, JWTError
from passlib.context import CryptContext
from pydantic import EmailStr
from sqlalchemy.orm import Session
from starlette.responses import HTMLResponse, RedirectResponse

from app.auth.models import User
from app.auth.sсhemas import UserResponse, TokenResponse
from app.database import get_db
from config import SECRET_KEY, ALGORITHM
from main import templates

router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Get sign-up page
@router.get("/sign-up", response_class=HTMLResponse)
async def sign_up_route(request: Request):
    return templates.TemplateResponse("sign-up.html", {"request": request})


# Sign-up response
@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
        response: Response,
        name: str = Form(min_length=3, max_length=16),
        email: str = Form(...),
        password: str = Form(min_length=8),
        db: Session = Depends(get_db)
):
    db_user = db.query(User).filter(User.email == email).first()
    if db_user:
        raise HTTPException(status_code=422, detail="email already registered")

    new_user = User(
        name=name,
        email=email
    )
    new_user.set_password(password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return RedirectResponse(url="/auth/sign-in", status_code=status.HTTP_303_SEE_OTHER)


# Get sign-in page
@router.get("/sign-in", response_class=HTMLResponse)
async def sign_in_route(request: Request):
    return templates.TemplateResponse("sign-in.html", {"request": request})


# Login response
@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def login_user(
        response: Response,
        email: str = Form(...),
        password: str = Form(...),
        db: Session = Depends(get_db)
):
    db_user = db.query(User).filter(User.email == email).first()
    if not db_user or not db_user.verify_password(password):
        raise HTTPException(status_code=400, detail="data incorrect")

    check = await authenticate_user(email=db_user.email, password=password, db=db)
    if check is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail='data incorrect')

    # Pass the 'response' to create_access_token
    access_token = create_access_token({"sub": str(check.id)}, response)
    return {'access_token': access_token, 'token_type': 'bearer', 'refresh_token': None}


# Logout response
@router.post("/logout")
async def logout_user(response: Response):
    response.delete_cookie(key="users_access_token")
    return {'message': 'The user has successfully logged out.'}


async def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, response: Response) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=30)
    to_encode.update({"exp": expire})
    auth_data = get_auth_data()
    encode_jwt = jwt.encode(to_encode, auth_data['secret_key'], algorithm=auth_data['algorithm'])

    response.set_cookie(key="users_access_token", value=encode_jwt, httponly=True, max_age=timedelta(days=30))

    return encode_jwt


async def authenticate_user(email: EmailStr, password: str, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == email).first()
    if not db_user or verify_password(plain_password=password, hashed_password=db_user.password) is False:
        return None
    return db_user


def get_auth_data():
    return {"secret_key": SECRET_KEY, "algorithm": ALGORITHM}


async def get_token(request: Request):
    token = request.cookies.get('users_access_token')
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Token not found')

    return token


async def get_current_user(token: str = Depends(get_token), db: Session = Depends(get_db)):
    try:
        auth_data = get_auth_data()
        payload = jwt.decode(token, auth_data['secret_key'], algorithms=[auth_data['algorithm']])
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Token invalid.')

    expire = payload.get('exp')
    expire_time = datetime.fromtimestamp(int(expire), tz=timezone.utc)
    if (not expire) or (expire_time < datetime.now(timezone.utc)):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='The token has expired.')

    user_id = payload.get('sub')
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='User ID not found')

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='User not found')

    return user


async def require_authentication(token: str = Depends(get_token), db: Session = Depends(get_db)):
    try:
        auth_data = get_auth_data()
        payload = jwt.decode(token, auth_data['secret_key'], algorithms=[auth_data['algorithm']])
        expire = payload.get('exp')
        expire_time = datetime.fromtimestamp(int(expire), tz=timezone.utc)

        if not expire or expire_time < datetime.now(timezone.utc):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

        user_id = payload.get('sub')
        if not user_id or not db.query(User).filter(User.id == user_id).first():
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized access")


async def admin_required(user: User = Depends(get_current_user)):
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_303_SEE_OTHER, detail="User is not admin!")
