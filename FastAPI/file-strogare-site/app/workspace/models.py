from datetime import datetime, timezone, timedelta

from sqlalchemy import Column, Integer, String, DateTime, Float, Table, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from app.database import Base

kyiv_timezone = timezone(timedelta(hours=2))

file_tag_association = Table(
    'file_tag_association',
    Base.metadata,
    Column('file_id', Integer, ForeignKey('files.id'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id'), primary_key=True)
)


class Tag(Base):
    __tablename__ = 'tags'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    count_files = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False,
                        default=lambda: datetime.now(kyiv_timezone).replace(microsecond=0))
    files_downloaded = Column(Integer, nullable=False, default=0)

    files = relationship('File', secondary=file_tag_association, back_populates="tags")


class File(Base):
    __tablename__ = 'files'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    file = Column(String, nullable=False)
    downloaded_times = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(kyiv_timezone).replace(microsecond=0))
    size = Column(Float, nullable=False, default=0)
    path_to_file = Column(String, nullable=False, default="/image/cat.jpg")
    status = Column(Boolean, nullable=False, default=True)
    tags = relationship("Tag", secondary=file_tag_association, back_populates="files")
    download_history = relationship("DownloadFilesHistory", back_populates="file")


class DownloadFilesHistory(Base):
    __tablename__ = 'download_files_history'

    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey('files.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    download_time = Column(DateTime, nullable=False, default=lambda: datetime.now(kyiv_timezone).replace(microsecond=0))

    file = relationship("File", back_populates="download_history")
    user = relationship("User", back_populates="download_history")
