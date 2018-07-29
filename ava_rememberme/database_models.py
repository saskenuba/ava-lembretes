import datetime

from passlib.hash import pbkdf2_sha256
from sqlalchemy import (JSON, Boolean, Column, DateTime, ForeignKey, Integer,
                        String, Text)
from sqlalchemy.orm import relationship

from ava_rememberme.database import Base
from ava_rememberme.exceptions import AssignmentExpired


class Users(Base):
    __tablename__ = 'Users'

    user_id = Column(Integer, primary_key=True)
    email = Column(String(50), unique=True)
    nome = Column(String(50))
    uninove_ra = Column(Text, unique=True)
    uninove_senha = Column(Text)
    active = Column(Boolean, default=False)
    confirmed_at = Column(DateTime, nullable=True)

    profile = relationship('Profiles', backref='Users', cascade='all')
    assignments = relationship('Assignments', backref='Users', cascade='all')

    def __init__(self, email, nome, uninove_ra, uninove_senha):
        self.email = email
        self.nome = nome
        self.uninove_ra = uninove_ra
        self.uninove_senha = uninove_senha

    def __repr__(self):
        return 'User Object: ID {}, Nome {}, Email {}, RA {}'.format(
            self.user_id, self.nome, self.email, self.uninove_ra)

    def isActive(self):
        return self.active

    def activate(self):
        self.active = True
        self.confirmed_at = datetime.datetime.now()

    def deactivate(self, ):
        self.active = False

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
    name = Column('Name', String(80))
    discipline = Column('Discipline', String(60))

    # tipo = questionario ou forum
    type = Column('Type', String(20))

    # time in days before assignment ends
    dueDate = Column('Due_Date', Integer)

    @staticmethod
    def get():
        return Assignments.query.all()

    def __repr__(self):
        return u'{} ID {}, Usuário {}, Dias Restantes: {}'.format(
            self.type, self.assignment_id, self.user_id, self.dueDate)

    def decreaseDay(self):
        if self.dueDate < 1:
            raise AssignmentExpired()
        self.dueDate -= 1


class Profiles(Base):
    __tablename__ = 'Profiles'

    user_id = Column(Integer, ForeignKey('Users.user_id'))
    profile_id = Column(Integer, primary_key=True)
    register_date = Column(DateTime, default=datetime.datetime.now)

    def __init__(self, user_id):
        "docstring"
        self.user_id = user_id
