"""
文章管理端点
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
import uuid
import logging
from datetime import datetime, timezone, timedelta

# 修正的导入路径
from app.core.database import get_db, engine, Base
from app.models import models as db_models  # 避免与FastAPI的models冲突
from app.crud import crud
from app.schemas import schemas

# 配置日志
logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(
    prefix="/posts",
    tags=['posts']
)

@router.post("/posts/", response_model=schemas.PostResponse)
def create_post(post: schemas.PostCreate, db: Session = Depends(get_db)):
    return crud.create_post(db=db, post=post)


@router.get("/posts/", response_model=List[schemas.PostResponse])
def read_posts(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    posts = crud.get_posts(db, skip=skip, limit=limit)
    return posts


@router.get("/posts/{post_id}", response_model=schemas.PostResponse)
def read_post(post_id: int, db: Session = Depends(get_db)):
    db_post = crud.get_post(db, post_id=post_id)
    if db_post is None:
        raise HTTPException(status_code=404, detail="文章不存在")
    return db_post


@router.delete("/posts/{post_id}", response_model=schemas.MessageResponse)
def delete_post(post_id: int, db: Session = Depends(get_db)):
    db_post = crud.delete_post(db, post_id=post_id)
    if db_post is None:
        raise HTTPException(status_code=404, detail="文章不存在")
    return {"message": "文章删除成功"}

# 添加实践到课堂

