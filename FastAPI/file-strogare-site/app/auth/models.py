from datetime import datetime, timezone, timedelta

from passlib.hash import bcrypt
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship

from app.database import Base

kyiv_timezone = timezone(timedelta(hours=2))


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    password = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False)
    latest_activity = Column(DateTime, nullable=False,
                             default=lambda: datetime.now(kyiv_timezone).replace(microsecond=0))
    files_downloaded = Column(Integer, nullable=False, default=0)
    download_history = relationship("DownloadFilesHistory", back_populates="user")

    def set_password(self, password: str):
        self.password = bcrypt.hash(password)

    def verify_password(self, password: str) -> bool:
        return bcrypt.verify(password, self.password)
