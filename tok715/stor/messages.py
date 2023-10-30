import time
from typing import List

from sqlalchemy import select, or_, and_
from sqlalchemy.orm import Session

from .model import Message
from .setup import VECTOR_VERSION, _state


def update_stale_messages(session: Session, limit=10):
    now_ts = int(time.time() * 1000)

    messages = session.scalars(
        select(Message).where(
            or_(
                # previous vector version
                Message.vector_version != VECTOR_VERSION,
                and_(
                    # current vector version
                    Message.vector_version == VECTOR_VERSION,
                    # not vectorized for 10 minutes
                    Message.vector_status == 0,
                    Message.ts < now_ts - 600 * 1000,
                ),
            )
        ).order_by(Message.ts.desc()).limit(limit)
    ).all()

    # filter out for vectorize
    to_vectorize = []

    for message in messages:
        if message.should_vectorize():
            to_vectorize.append(message)
        else:
            # update vector_status = -1 for ignored
            message.vector_status = -1

    if to_vectorize:
        vectors = _state.ai_service.invoke_embeddings(
            [item.content for item in to_vectorize],
        )
        _save_message_vectors(to_vectorize, vectors)

        # update vector_status for to_vectorize
        for message in to_vectorize:
            message.vector_status = 1

    # update all vector_version
    for message in messages:
        message.vector_status = VECTOR_VERSION

    session.commit()


def fetch_recent_messages(session: Session, limit=20) -> List[Message]:
    return list(reversed(session.scalars(
        select(
            Message
        ).order_by(Message.ts.desc()).limit(limit)
    ).all()))


def add_message(session: Session, **kwargs) -> Message:
    kwargs.update(vector_version=VECTOR_VERSION)

    msg = Message(**kwargs)
    if msg.should_vectorize():
        # first stage
        msg.vector_status = 0
        session.add(msg)
        session.commit()

        # fetch and save vectors
        vectors = _state.ai_service.invoke_embeddings(
            [msg.content],
        )
        _save_message_vectors([msg], vectors)

        # second stage
        msg.vector_status = 1
        session.commit()
    else:
        msg.vector_status = -1
        session.add(msg)
        session.commit()

    return msg


def _save_message_vectors(items: List[Message], vectors: List[List[float]]):
    _state.collection_messages.upsert([
        [item.id for item in items],
        [item.user_group for item in items],
        [item.ts for item in items],
        vectors,
    ])
