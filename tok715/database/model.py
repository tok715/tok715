from sqlalchemy import String, Text, BigInteger, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Message(Base):
    __tablename__ = 'messages'

    # message id, same id is used in milvus also
    id: Mapped[int] = mapped_column(BigInteger(), name="id", primary_key=True)

    user_id: Mapped[str] = mapped_column(String(128), name="user_id", nullable=False, index=True)
    user_group: Mapped[str] = mapped_column(String(128), name="user_group", nullable=False, index=True)
    user_display_name: Mapped[str] = mapped_column(String(128), name="user_display_name", nullable=False)

    content: Mapped[str] = mapped_column(Text(), name="content")

    # unix timestamp in milliseconds
    ts: Mapped[int] = mapped_column(BigInteger(), name="ts", nullable=False, index=True)

    # 0: not processed
    # 1: processed
    # -1: ignored
    vector_status: Mapped[int] = mapped_column(Integer(), name="vector_status", nullable=False, index=True, default=0)

    # vector version
    vector_version: Mapped[int] = mapped_column(Integer(), name="vector_version", nullable=False, index=True, default=0)


def message_should_vectorize(msg: Message) -> bool:
    return len(msg.content) > 10
