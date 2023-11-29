from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import text
from sqlalchemy.sql.sqltypes import TIMESTAMP
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime


db = SQLAlchemy()


class Memory(db.Model):
    #__tablename__ = 'memories'
    __tablename__ = 'omr'
    id = Column(Integer, primary_key=True, nullable=False)
    user_message = Column(String, nullable=False)
    llm_response = Column(String, nullable=False)
    conversations_summary = Column(String, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow)

    owner_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=True)

    ## Define the one-to-many relationship with HumanMessage
    #user_messages = relationship('HumanMessage', back_populates='memory')

    def __repr__(self):
        return f"<Memory {self.id}>"


class User(db.Model):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, nullable=False)
    email = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"<User {self.id}>"



#class HumanMessage(db.Model):
#    __tablename__ = 'human_messages'
#    id = Column(Integer, primary_key=True, nullable=False)
#    content = Column(String, nullable=False)
#    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
#
#    # Define the foreign key relationship to Memory
#    memory_id = Column(Integer, ForeignKey('memories.id'), nullable=False)
#    memory = relationship('Memory', back_populates='user_messages')
#
#    def __repr__(self):
#        return f"<HumanMessage {self.id}>"
