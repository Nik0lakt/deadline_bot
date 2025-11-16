from __future__ import annotations

from datetime import datetime, date
from typing import Optional, List

from sqlalchemy import (
    BigInteger,
    Date,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class User(Base):
    __tablename__ = "users"  # 👈 явное имя

    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id: Mapped[Optional[int]] = mapped_column(BigInteger, unique=True, index=True, nullable=True)
    username: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(255))
    last_name: Mapped[Optional[str]] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    tasks_assigned: Mapped[List["Task"]] = relationship(
        back_populates="assignee", foreign_keys="Task.assignee_id"
    )
    tasks_created: Mapped[List["Task"]] = relationship(
        back_populates="creator", foreign_keys="Task.creator_id"
    )


class Chat(Base):
    __tablename__ = "chats"  # 👈 явное имя

    id: Mapped[int] = mapped_column(primary_key=True)
    tg_chat_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    title: Mapped[Optional[str]] = mapped_column(String(255))
    type: Mapped[Optional[str]] = mapped_column(String(32))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    tasks: Mapped[List["Task"]] = relationship(back_populates="chat")


class Task(Base):
    __tablename__ = "tasks"  # 👈 явное имя

    id: Mapped[int] = mapped_column(primary_key=True)

    chat_id: Mapped[int] = mapped_column(ForeignKey("chats.id", ondelete="RESTRICT"))
    creator_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    assignee_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))

    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    deadline: Mapped[date] = mapped_column(Date, index=True)

    status: Mapped[str] = mapped_column(String(20), index=True, default="open")  # open/done/canceled

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    origin_message_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)

    chat: Mapped["Chat"] = relationship(back_populates="tasks")
    creator: Mapped["User"] = relationship(back_populates="tasks_created", foreign_keys=[creator_id])
    assignee: Mapped["User"] = relationship(back_populates="tasks_assigned", foreign_keys=[assignee_id])

    __table_args__ = (
        Index("tasks_assignee_status_idx", "assignee_id", "status"),
        
    )
