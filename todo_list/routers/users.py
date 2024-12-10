from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from todo_list.database import get_session
from todo_list.models import User
from todo_list.schemas import Message, UserList, UserPublic, UserSchema
from todo_list.security import get_current_user, get_password_hash

router = APIRouter(prefix='/users', tags=['users'])
T_Session = Annotated[Session, Depends(get_session)]
T_CurrentUser = Annotated[User, Depends(get_current_user)]


@router.get('/{user_id}', response_model=UserPublic)
def get_user(user_id: int, session: T_Session):
    db_user = session.scalar(select(User).where(User.id == user_id))
    if not db_user:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='User not found')
    return db_user


@router.get('/', response_model=UserList)
def get_users(session: T_Session, current_user: T_CurrentUser, limit: int = 10, offset: int = 0):
    users = session.scalars(select(User).limit(limit=limit).offset(offset=offset))
    return {'users': users}


@router.post('/', response_model=UserPublic, status_code=HTTPStatus.CREATED)
def create_user(user: UserSchema, session: T_Session):
    db_user = session.scalar(select(User).where((User.username == user.username) | (User.email == user.email)))

    if db_user:
        if db_user.username == user.username:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail='Username already exists',
            )
        elif db_user.email == user.email:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail='Email already exists',
            )

    db_user = User(username=user.username, password=get_password_hash(user.password), email=user.email)

    session.add(db_user)
    session.commit()
    session.refresh(db_user)

    return db_user


@router.put('/{user_id}', response_model=UserPublic)
def update_user(user_id: int, user: UserSchema, session: T_Session, current_user: T_CurrentUser):
    if current_user.id != user_id:
        raise HTTPException(status_code=HTTPStatus.FORBIDDEN, detail='Not enough permission')
    current_user.username = user.username
    current_user.password = get_password_hash(user.password)
    current_user.email = user.email

    session.commit()
    session.refresh(current_user)

    return current_user


@router.delete('/{user_id}', response_model=Message)
def delete_user(user_id: int, session: T_Session, current_user: T_CurrentUser):
    if current_user.id != user_id:
        raise HTTPException(status_code=HTTPStatus.FORBIDDEN, detail='Not enough permission')
    session.delete(current_user)
    session.commit()

    return {'message': 'User deleted'}
