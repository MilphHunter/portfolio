import os
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from os import getenv

from fastapi import FastAPI, Depends, HTTPException, status, Form, Request, Response, BackgroundTasks
from fastapi.responses import RedirectResponse
from pydantic import EmailStr
from sqlalchemy import select, insert, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from starlette.templating import Jinja2Templates

from db import engine, Base, SessionLocal
from models import User, EmailVerification
from schemas import SignupIn, UserOut, CodeIn
from security import hash_password, generate_6_code, verify_password

from other import create_cookie, send_verification_email

templates = Jinja2Templates(directory="templates")
app = FastAPI()


# Инициализация БД при старте приложения.
@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# Возвращает асинхронную сессию БД (Depends).
async def get_db():
    async with SessionLocal() as session:
        yield session


# Отдаёт страницу регистрации.
@app.get("/signup")
async def signup_page(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})


# Регистрирует пользователя через JSON API.
@app.post("/api/signup", response_model=UserOut, status_code=201)
async def api_signup(payload: SignupIn, db: AsyncSession = Depends(get_db)):
    user = User(
        first_name=payload.first_name.strip(),
        last_name=payload.last_name.strip(),
        email=payload.email,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email уже зарегистрирован",
        )
    await db.refresh(user)
    return user


# Регистрирует пользователя через форму и отправляет код подтверждения.
@app.post("/signup-form", status_code=303)
async def signup_form(
        background: BackgroundTasks,
        first_name: str = Form(...),
        last_name: str = Form(...),
        email: EmailStr = Form(...),
        password: str = Form(...),
        db: AsyncSession = Depends(get_db),
):
    payload = SignupIn(first_name=first_name, last_name=last_name, email=email, password=password)
    user_cookie = create_cookie()
    user = User(
        first_name=payload.first_name.strip(),
        last_name=payload.last_name.strip(),
        email=payload.email,
        password_hash=hash_password(payload.password),
        session_cookie=user_cookie
    )
    db.add(user)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Email уже зарегистрирован")

    await db.refresh(user, attribute_names=["id"])

    code = generate_6_code()
    code_h = hash_password(code)

    ttl_min = int(getenv("VERIFICATION_TTL_MIN", "30"))
    expires = datetime.now(timezone.utc) + timedelta(minutes=ttl_min)

    await db.execute(
        insert(EmailVerification).values(
            user_id=user.id,
            code_hash=code_h,
            expires_at=expires,
            attempts_left=5,
        )
    )
    await db.commit()

    background.add_task(send_verification_email, str(payload.email), code)

    response = RedirectResponse(url="/confirmation", status_code=303)
    response.set_cookie(
        key="session_cookie",
        value=user_cookie,
        httponly=True,
        max_age=60 * 60 * 24 * 30,
        samesite="lax",
        secure=False
    )
    return response


# Показывает страницу подтверждения email по сессии.
@app.get("/confirmation")
async def confirmation_page(
        request: Request,
        db: AsyncSession = Depends(get_db),
):
    sess = request.cookies.get("session_cookie")
    if not sess:
        return templates.TemplateResponse(
            "confirmation.html",
            {"request": request, "error": "Сессия не найдена. Войдите заново."},
            status_code=401,
        )

    stmt = select(User.email).where(User.session_cookie == sess)
    result = await db.execute(stmt)
    email = result.scalar_one_or_none()

    if email is None:
        resp = templates.TemplateResponse(
            "confirmation.html",
            {"request": request, "error": "Сессия недействительна. Войдите заново."},
            status_code=401,
        )
        resp.delete_cookie("session_cookie")
        return resp

    return templates.TemplateResponse(
        "confirmation.html",
        {"request": request, "email": email},
    )


# Проверяет введённый код и переводит на профиль.
@app.post("/confirm")
async def confirm_code(
        request: Request,
        code: str = Form(...),
        db: AsyncSession = Depends(get_db),
):
    sess = request.cookies.get("session_cookie")
    if not sess:
        raise HTTPException(status_code=401, detail="Сессия отсутствует")

    user_id = await db.scalar(select(User.id).where(User.session_cookie == sess))
    if not user_id:
        raise HTTPException(status_code=401, detail="Некорректная сессия")

    row = await db.execute(
        select(EmailVerification)
        .where(EmailVerification.user_id == user_id)
        .order_by(EmailVerification.id.desc())
        .limit(1)
    )
    ver: EmailVerification | None = row.scalar_one_or_none()
    if not ver:
        raise HTTPException(status_code=400, detail="Код не запрошен")

    now_utc = datetime.now(timezone.utc)

    if ver.expires_at < now_utc:
        raise HTTPException(status_code=400, detail="Код истёк")
    if ver.attempts_left <= 0:
        raise HTTPException(status_code=400, detail="Превышено число попыток")

    if not verify_password(code, ver.code_hash):
        await db.execute(
            update(EmailVerification)
            .where(EmailVerification.id == ver.id)
            .values(attempts_left=ver.attempts_left - 1)
        )
        await db.commit()
        raise HTTPException(status_code=400, detail="Неверный код")

    await db.execute(delete(EmailVerification).where(EmailVerification.id == ver.id))
    await db.commit()
    return RedirectResponse(url="/profile", status_code=303)


# Отдаёт страницу профиля авторизованного пользователя.
@app.get("/profile")
async def profile_page(
        request: Request,
        db: AsyncSession = Depends(get_db),
):
    sess = request.cookies.get("session_cookie")
    if not sess:
        return templates.TemplateResponse(
            "confirmation.html",
            {"request": request, "error": "Сессия не найдена. Войдите заново."},
            status_code=401,
        )

    stmt = select(
        User.id,
        User.first_name,
        User.last_name,
        User.balance,
        User.two_factor_enabled,
    ).where(User.session_cookie == sess)

    result = await db.execute(stmt)
    row = result.one_or_none()

    if row is None:
        resp = templates.TemplateResponse(
            "confirmation.html",
            {"request": request, "error": "Сессия недействительна. Войдите заново."},
            status_code=401,
        )
        resp.delete_cookie("session_cookie")
        return resp

    user_id, first_name, last_name, balance, two_factor_enabled = row

    if None in (user_id, first_name, last_name, balance, two_factor_enabled):
        resp = templates.TemplateResponse(
            "confirmation.html",
            {"request": request, "error": "Сессия недействительна. Войдите заново."},
            status_code=401,
        )
        resp.delete_cookie("session_cookie")
        return resp

    return templates.TemplateResponse(
        "profile.html",
        {
            "request": request,
            "user_id": user_id,
            "first_name": first_name,
            "last_name": last_name,
            "balance": balance,
            "two_factor_enabled": two_factor_enabled,  # <-- важно передать
        },
    )


# Включает/выключает 2FA для текущего пользователя.
@app.post("/toggle-2fa")
async def toggle_2fa(request: Request, db: AsyncSession = Depends(get_db)):
    data = await request.json()
    enabled = bool(data.get("enabled"))

    sess = request.cookies.get("session_cookie")
    if not sess:
        return {"ok": False, "message": "Нет активной сессии"}

    user = await db.scalar(select(User).where(User.session_cookie == sess))
    if not user:
        return {"ok": False, "message": "Пользователь не найден"}

    user.two_factor_enabled = enabled
    await db.commit()
    return {"ok": True, "enabled": enabled}


# Округляет Decimal до двух знаков банковским правилом.
def q2(v: Decimal) -> Decimal:
    return v.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


# Выполняет перевод средств между пользователями (атомарно).
@app.post("/send_money-form")
async def send_money_form(
        request: Request,
        amount: str = Form(...),
        email: EmailStr = Form(...),
        db: AsyncSession = Depends(get_db),
):
    sess_cookie_name = "session_cookie"
    sess = request.cookies.get(sess_cookie_name)
    if not sess:
        return {"ok": False, "message": "Сессия не найдена. Войдите в аккаунт снова."}

    try:
        amt = Decimal(amount.replace(",", "."))
    except (InvalidOperation, AttributeError):
        return {"ok": False, "message": "Укажите корректную сумму перевода."}

    if amt <= Decimal("0"):
        return {"ok": False, "message": "Сумма должна быть больше 0."}

    amt = q2(amt)

    try:
        async with db.begin():
            sender = await db.scalar(
                select(User).where(User.session_cookie == sess).with_for_update()
            )
            if not sender:
                return {"ok": False, "message": "Пользователь не найден. Повторите вход."}

            if sender.email.lower() == email.lower():
                return {"ok": False, "message": "Нельзя отправить перевод самому себе."}

            recipient = await db.scalar(
                select(User).where(User.email == email).with_for_update()
            )
            if not recipient:
                return {"ok": False, "message": "Получатель с таким e-mail не найден."}

            sender_balance = Decimal(sender.balance)
            if sender_balance < amt:
                return {"ok": False, "message": "Недостаточно средств на балансе."}

            sender.balance = q2(sender_balance - amt)

            recipient.balance = q2(Decimal(recipient.balance) + amt)

        return {
            "ok": True,
            "message": "Перевод выполнен успешно.",
            "new_balance": str(q2(Decimal(sender.balance))),
        }

    except HTTPException as e:
        raise e
    except Exception:
        return {
            "ok": False,
            "message": "Не удалось выполнить перевод. Попробуйте позже.",
        }


# Удаляет cookie сессии и перенаправляет на логин.
@app.post("/logout")
async def logout(response: Response):
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("session_cookie")
    return response


# Отдаёт страницу логина.
@app.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


# Авторизует пользователя, при 2FA — шлёт код и редиректит.
@app.post("/login-form")
async def login_form(
        request: Request,
        background: BackgroundTasks,
        db: AsyncSession = Depends(get_db),
        email: str = Form(...),
        password: str = Form(...),
        remember: bool = Form(False),
):
    stmt = select(User.id, User.email, User.password_hash, User.two_factor_enabled).where(User.email == email)
    result = await db.execute(stmt)
    row = result.one_or_none()

    if row is None:
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "error_general": "Неверный email или пароль.",
                "error_email": "Проверьте корректность email.",
                "form_email": email,
            },
            status_code=400,
        )

    user_id, user_email, password_hash, twofa = row

    if not verify_password(password, password_hash):
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "error_general": "Неверный email или пароль.",
                "error_password": "Пароль не подходит.",
                "form_email": email,
            },
            status_code=400,
        )

    session_token = create_cookie()
    user = await db.get(User, user_id)
    user.session_cookie = session_token
    await db.commit()

    if remember:
        max_age = 60 * 60 * 24 * 30  # 30 дней
    else:
        max_age = None  # сессионная

    if twofa:
        await db.refresh(user, attribute_names=["id"])

        code = generate_6_code()
        code_h = hash_password(code)

        ttl_min = int(os.getenv("VERIFICATION_TTL_MIN", "30"))
        expires = datetime.now(timezone.utc) + timedelta(minutes=ttl_min)

        await db.execute(
            insert(EmailVerification).values(
                user_id=user.id,
                code_hash=code_h,
                expires_at=expires,
                attempts_left=5,
            )
        )
        await db.commit()

        background.add_task(send_verification_email, user.email, code)

        resp = RedirectResponse(url="/confirmation", status_code=303)
        resp.set_cookie(
            "session_cookie",
            session_token,
            max_age=max_age,
            httponly=True,
            samesite="lax",
            secure=False if os.getenv("ENV") == "dev" else True,  # True в проде/HTTPS
            path="/",
        )
        return resp

    resp = RedirectResponse(url="/profile", status_code=303)
    resp.set_cookie(
        "session_cookie",
        session_token,
        max_age=max_age,
        httponly=True,
        samesite="lax",
        secure=False if os.getenv("ENV") == "dev" else True,
        path="/",
    )
    return resp
