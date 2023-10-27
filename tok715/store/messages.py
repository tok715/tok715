import time
from typing import Sequence

from sqlalchemy import select, or_, and_

from .model import Message
from .store import VECTOR_VERSION, _state, create_session, _save_message_vectors


def update_stale_messages(limit=10):
    now_ts = int(time.time() * 1000)

    with create_session() as session:
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


def fetch_recent_messages(limit=20) -> Sequence[Message]:
    with create_session() as session:
        return session.scalars(
            select(
                Message
            ).order_by(Message.ts.desc()).limit(limit)
        ).all()


def add_message(**kwargs) -> Message:
    kwargs.update(vector_version=VECTOR_VERSION)

    with create_session() as session:
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
