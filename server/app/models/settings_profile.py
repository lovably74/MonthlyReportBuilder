"""SettingsProfile ORM model definition."""

from sqlalchemy import Boolean, Column, Index, Integer, Text

from app.core.database import Base


class SettingsProfile(Base):
    """환경설정 프로필 ORM 모델.

    Columns:
        id: 프로필 고유 ID (PRIMARY KEY AUTOINCREMENT)
        name: 프로필명 (1~50자, UNIQUE, NOT NULL)
        description: 프로필 설명 (최대 200자, DEFAULT '')
        is_default: 기본 프로필 여부 (NOT NULL, DEFAULT FALSE)
        created_at: 생성 시각 (ISO 8601 TEXT, NOT NULL)
        updated_at: 수정 시각 (ISO 8601 TEXT, NOT NULL)
    """

    __tablename__ = "settings_profile"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False, unique=True)
    description = Column(Text, nullable=False, default="")
    is_default = Column(Boolean, nullable=False, default=False)
    created_at = Column(Text, nullable=False)
    updated_at = Column(Text, nullable=False)

    __table_args__ = (
        Index("idx_profile_name", "name", unique=True),
        Index("idx_profile_is_default", "is_default"),
        Index("idx_profile_updated_at", "updated_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<SettingsProfile(id={self.id}, name='{self.name}', "
            f"is_default={self.is_default})>"
        )
