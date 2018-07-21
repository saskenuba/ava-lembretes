from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime, JSON
from sqlalchemy.orm import relationship
from passlib.hash import pbkdf2_sha256
from ava_rememberme.database import Base
import datetime


class Users(Base):
    __tablename__ = 'Users'

    user_id = Column(Integer, primary_key=True)
    email = Column(String(50), unique=True)
    nome = Column(String(50))
    uninove_ra = Column(Text, unique=True)
    uninove_senha = Column(Text)
    profile = relationship('Profiles', backref='Users', cascade='all')
    assignment = relationship('Assignments', backref='Users', cascade='all')

    def __init__(self, email, nome, uninove_ra, uninove_senha):
        self.email = email
        self.nome = nome
        self.uninove_ra = uninove_ra
        self.uninove_senha = uninove_senha

    def __repr__(self):
        return 'User Object: ID {}, Email {}, RA {}'.format(
            self.user_id, self.email, self.uninove_ra)

    @staticmethod
    def get():
        return Users.query.all()

    @staticmethod
    def hashString(string):
        return pbkdf2_sha256.hash(string)

    @staticmethod
    def hashVerify(self, string):
        return pbkdf2_sha256.verify(string, self.senha)


class Assignments(Base):
    __tablename__ = 'Assignments'

    user_id = Column(Integer, ForeignKey('Users.user_id'))
    assignment_id = Column(Integer, primary_key=True)
    questionario = Column(JSON)
    forum = Column(JSON)


class Profiles(Base):
    __tablename__ = 'Profiles'

    user_id = Column(Integer, ForeignKey('Users.user_id'))
    profile_id = Column(Integer, primary_key=True)
    register_date = Column(DateTime, default=datetime.datetime.now)

    def __init__(self, user_id):
        "docstring"
        self.user_id = user_id
