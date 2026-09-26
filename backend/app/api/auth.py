from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.models.database import get_db, User, generate_uuid
from backend.app.models.schemas import LoginRequest, TokenResponse, UserResponse
from backend.app.core.security import verify_password, get_password_hash, create_access_token, get_current_user_optional

router = APIRouter(prefix="/auth", tags=["Authentication & RBAC"])

DEMO_USERS = {
    "verifier": {"password": "verifier123", "role": "VERIFIER", "name": "Inspector Rajesh Nair (Border Control)"},
    "investigator": {"password": "investigator123", "role": "INVESTIGATOR", "name": "Senior Forensic Analyst S. Rao"},
    "admin": {"password": "admin123", "role": "ADMIN", "name": "System Administrator (MHA Cyber Command)"}
}

def seed_demo_users_if_needed(db: Session):
    for uname, info in DEMO_USERS.items():
        existing = db.query(User).filter(User.username == uname).first()
        if not existing:
            user = User(
                id=generate_uuid(),
                username=uname,
                email=f"{uname}@trustid.gov.in",
                hashed_password=get_password_hash(info["password"]),
                full_name=info["name"],
                role=info["role"],
                is_active=True
            )
            db.add(user)
    db.commit()

@router.post("/login", response_model=TokenResponse, summary="Secure authentication for Verifiers, Investigators & Admins")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    seed_demo_users_if_needed(db)
    user = db.query(User).filter(User.username == req.username).first()

    # Check database or fallback to demo dictionary
    valid = False
    role = "VERIFIER"
    user_data = {}

    if user and verify_password(req.password, user.hashed_password):
        valid = True
        role = user.role
        user_data = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role
        }
    elif req.username in DEMO_USERS and DEMO_USERS[req.username]["password"] == req.password:
        valid = True
        role = DEMO_USERS[req.username]["role"]
        user_data = {
            "id": f"usr-{req.username}",
            "username": req.username,
            "email": f"{req.username}@trustid.gov.in",
            "full_name": DEMO_USERS[req.username]["name"],
            "role": role
        }

    if not valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials. Use demo accounts: verifier/verifier123, investigator/investigator123, or admin/admin123."
        )

    token = create_access_token(subject=user_data["username"], role=role)
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=user_data
    )

@router.get("/me", summary="Get profile of currently logged-in user")
def get_current_user_profile(user: dict = Depends(get_current_user_optional), db: Session = Depends(get_db)):
    seed_demo_users_if_needed(db)
    db_user = db.query(User).filter(User.username == user.get("username")).first()
    if db_user:
        return {
            "id": db_user.id,
            "username": db_user.username,
            "email": db_user.email,
            "full_name": db_user.full_name,
            "role": db_user.role
        }
    return {
        "id": "usr-default",
        "username": user.get("username", "verifier"),
        "email": f"{user.get('username', 'verifier')}@trustid.gov.in",
        "full_name": "Active Screening Officer",
        "role": user.get("role", "VERIFIER")
    }
