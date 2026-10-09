from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.dependencies import require_roles
from app.database.connection import get_db
from app.database.models import Person


router = APIRouter(
    prefix="/people",
    tags=["People"],
)


class PersonCreate(BaseModel):
    full_name: str
    date_of_birth: str
    gender: str
    address: str
    identity_number: str
    phone: str
    email: str


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
)
def register_person(
    person_data: PersonCreate,
    db: Session = Depends(get_db),
    current_admin=Depends(
        require_roles(
            "ADMIN",
            "SUPER_ADMIN",
        )
    ),
):
    existing_person = (
        db.query(Person)
        .filter(
            Person.identity_number == person_data.identity_number
        )
        .first()
    )

    if existing_person:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Identity number is already registered",
        )

    person = Person(
        full_name=person_data.full_name,
        date_of_birth=person_data.date_of_birth,
        gender=person_data.gender,
        address=person_data.address,
        identity_number=person_data.identity_number,
        phone=person_data.phone,
        email=person_data.email,
        is_active=True,
    )

    try:
        db.add(person)
        db.commit()
        db.refresh(person)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Identity could not be registered",
        )

    return {
        "message": "Identity registered successfully",
        "person": {
            "id": person.id,
            "full_name": person.full_name,
            "identity_number": person.identity_number,
            "date_of_birth": person.date_of_birth,
            "gender": person.gender,
            "phone": person.phone,
            "email": person.email,
            "is_active": person.is_active,
        },
    }


@router.get(
    "/",
)
def list_people(
    db: Session = Depends(get_db),
    current_admin=Depends(
        require_roles(
            "ADMIN",
            "SUPER_ADMIN",
        )
    ),
):
    people = (
        db.query(Person)
        .filter(Person.is_active == True)
        .order_by(Person.id.asc())
        .all()
    )

    return {
        "people": [
            {
                "id": person.id,
                "full_name": person.full_name,
                "identity_number": person.identity_number,
                "date_of_birth": person.date_of_birth,
                "gender": person.gender,
                "phone": person.phone,
                "email": person.email,
                "is_active": person.is_active,
            }
            for person in people
        ]
    }


@router.get(
    "/{person_id}",
)
def get_person(
    person_id: int,
    db: Session = Depends(get_db),
    current_admin=Depends(
        require_roles(
            "ADMIN",
            "SUPER_ADMIN",
        )
    ),
):
    person = (
        db.query(Person)
        .filter(
            Person.id == person_id,
            Person.is_active == True,
        )
        .first()
    )

    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Person not found",
        )

    return {
        "person": {
            "id": person.id,
            "full_name": person.full_name,
            "identity_number": person.identity_number,
            "date_of_birth": person.date_of_birth,
            "gender": person.gender,
            "address": person.address,
            "phone": person.phone,
            "email": person.email,
            "is_active": person.is_active,
        }
    }