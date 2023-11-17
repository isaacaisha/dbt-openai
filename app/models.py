from sqlalchemy import Column, String, Integer
from sqlalchemy.sql.expression import text
from sqlalchemy.sql.sqltypes import TIMESTAMP
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Memory(db.Model):
    __tablename__ = 'memories'
    id = Column(Integer, primary_key=True, nullable=False)
    user_message = Column(String, nullable=False)
    llm_response = Column(String, nullable=False)
    conversations_summary = Column(String, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))

    def __repr__(self):
        return f"<Memory {self.id}>"
