# job_agent/models.py
from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, UniqueConstraint, create_engine, Text
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

Base = declarative_base()

class Job(Base):
    __tablename__ = "jobs"
    id = Column(Integer, primary_key=True)
    source = Column(String(64), index=True)
    external_id = Column(String(256))      # GUID/URL/hash from source
    title = Column(String(512), index=True)
    company = Column(String(256), index=True)
    location = Column(String(256), index=True)
    url = Column(String(1024))
    description = Column(Text)
    published_at = Column(DateTime, index=True)
    salary = Column(Float, nullable=True)
    raw = Column(Text)                     # stash full JSON/text if helpful
    seen_at = Column(DateTime, default=datetime.utcnow)
    notified = Column(Boolean, default=False)

    __table_args__ = (UniqueConstraint("source", "external_id", name="uq_source_external"),)

def get_session(db_path="sqlite:///jobs.db"):
    engine = create_engine(db_path, future=True)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, future=True)()
