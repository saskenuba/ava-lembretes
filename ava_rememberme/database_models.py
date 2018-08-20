import datetime

from passlib.hash import pbkdf2_sha256
from sqlalchemy import (JSON, Boolean, Column, DateTime, ForeignKey, Integer,
                        String, Table, Text)
from sqlalchemy.schema import Index
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import backref, relationship

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

    # one to one
    # user has one profile
    profile = relationship('Profiles', backref='Users', cascade='all')

    # association proxy of "user_keywords" collection
    # to "keyword" attribute
    assignments = association_proxy(
        'user_assignments',
        'assignments',
        creator=lambda assignments: Users_Assignments(assignments=assignments[0], userCompleted=assignments[1]))

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


users_disciplines = Table(
    'Users_Disciplines', Base.metadata,
    Column('StudentID', Integer, ForeignKey('Users.user_id')),
    Column('DisciplineID', Integer, ForeignKey('Disciplines.DisciplineID')))


class Users_Assignments(Base):
    __tablename__ = 'Users_Assignments'

    user_id = Column(Integer, ForeignKey('Users.user_id'), primary_key=True)
    assignment_id = Column(
        Integer, ForeignKey('Assignments.assignment_id'), primary_key=True)
    userCompleted = Column('UserCompleted', Boolean, nullable=False)

    #Index('idx_user_assignment', 'user_id', 'assignment_id')

    # bidirectional attribute/collection of "user"/"user_assignments"
    users = relationship(
        'Users',
        backref=backref("user_assignments", cascade="all, delete-orphan"))

    def __init__(self, assignments=None, userCompleted=False):
        "docstring"
        self.assignments = assignments
        self.userCompleted = userCompleted

    # reference to the "Assignments" object
    assignments = relationship("Assignments")


class Disciplines(Base):
    __tablename__ = 'Disciplines'

    discipline_id = Column('DisciplineID', Integer, primary_key=True)
    name = Column('Name', String(60))
    isOnline = Column('isOnline', Boolean)
    idCurso = Column('IdCurso', Integer)
    codCurso = Column('CodCurso', Integer)

    # relationships
    # one discipline has many assignments
    assignments = relationship(
        'Assignments', backref='Disciplines', cascade='all')
    users = relationship(
        'Users', secondary=users_disciplines, backref='Disciplines')

    def __init__(self, user_id, name, isOnline, idCurso, codCurso):
        self.user_id = user_id
        self.name = name
        self.isOnline = isOnline
        self.idCurso = idCurso
        self.codCurso = codCurso

    def __repr__(self):
        return u'Disciplina: {} - ID {} - Online: {}'.format(
            self.name, self.discipline_id, self.isOnline)


class Assignments(Base):
    __tablename__ = 'Assignments'

    assignment_id = Column(Integer, primary_key=True)
    discipline_id = Column('DisciplineID', Integer,
                           ForeignKey('Disciplines.DisciplineID'))
    name = Column('Name', String(80))
    codigo = Column('Codigo', Integer, index=True)

    # tipo = questionario ou forum
    type = Column('Type', String(20))

    # time in days before assignment ends
    dueDate = Column('Due_Date', DateTime)

    # many to many
    # multiple users can have multiple assignments

    def __init__(self, name, codigo, discipline_id, type, dueDate):
        "docstring"
        self.name = name
        self.codigo = codigo
        self.discipline_id = discipline_id
        self.type = type
        self.dueDate = dueDate

    @staticmethod
    def get():
        return Assignments.query.all()

    def __repr__(self):
        return u'{} ID {}, Usuário {}, Dias Restantes: {}'.format(
            self.type, self.assignment_id, self.user_id, self.dueDate)

    @property
    def daysLeft(self):
        remainingDays = self.dueDate - datetime.datetime.now()
        if remainingDays.days < 1:
            raise AssignmentExpired()
        return remainingDays.days


class Profiles(Base):
    __tablename__ = 'Profiles'

    profile_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('Users.user_id'))
    register_date = Column(DateTime, default=datetime.datetime.now)

    def __init__(self, user_id):
        "docstring"
        self.user_id = user_id
