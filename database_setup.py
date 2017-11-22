import os
import sys

from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)


class ThoughtPod(Base):

    __tablename__ = 'thought_pod'

    pod_title = Column(String(80), nullable=False)
    description = Column(String(250))
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'pod_title': self.pod_title,
            'description': self.description,
            'id': self.id,
        }


class PodItem(Base):

    __tablename__ = 'pod_item'

    title = Column(String(80), nullable=False)
    id = Column(Integer, primary_key=True)
    url = Column(String(250))
    description = Column(String(250))
    time_investment = Column(String(80))
    difficulty_level = Column(Integer)
    thought_pod_id = Column(Integer, ForeignKey('thought_pod.id'))
    thought_pod = relationship(ThoughtPod)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'title': self.title,
            'url': self.url,
            'description': self.description,
            'time_investment': self.time_investment,
            'difficulty_level': self.difficulty_level,
            'id': self.id,
        }


engine = create_engine('sqlite:///thoughtpods.db')
Base.metadata.create_all(engine)
