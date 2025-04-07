from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    fullname = Column(String)
    email = Column(String, unique=True)
    password = Column(String)
    departement_id = Column(Integer, ForeignKey('departments.id'))
    
    # Relations
    department = relationship("Department", back_populates="users")
    clients = relationship("Client", back_populates="sales_contact")
    contracts = relationship("Contract", back_populates="sales_contact")
    events = relationship("Event", back_populates="support_contact")
    
    def __repr__(self):
        return f"User(fullname='{self.fullname}', email='{self.email}')"
    
    
class Client(Base):
    __tablename__ = 'clients'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    fullname = Column(String)
    email = Column(String, unique=True)
    phone_number = Column(Integer)
    enterprise = Column(String)
    create_date = Column(DateTime)
    update_date = Column(DateTime)
    sales_contact_id = Column(Integer, ForeignKey('users.id'))
    
    # Relations
    sales_contact = relationship("User", back_populates="clients")
    contracts = relationship("Contract", back_populates="client")
    events = relationship("Event", back_populates="client")
    
    def __repr__(self):
        return f"Client(fullname='{self.fullname})"
    
    
class Contract(Base):
    __tablename__ = 'contracts'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(Integer, ForeignKey('clients.id'))
    amount = Column(Float)
    remaining_amount = Column(Float)
    create_date = Column(DateTime)
    status = Column(Boolean)
    sales_contact_id = Column(Integer, ForeignKey('users.id'))
    
    # Relations
    client = relationship("Client", back_populates="contracts")
    sales_contact = relationship("User", back_populates="contracts")
    events = relationship("Event", back_populates="contract")

class Event(Base):
    __tablename__ = 'events'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    contract_id = Column(Integer, ForeignKey('contracts.id'))
    client_id = Column(Integer, ForeignKey('clients.id'))
    client_name = Column(String)
    client_contact = Column(String)
    start_event = Column(DateTime)
    end_event = Column(DateTime)
    location = Column(String)
    support_contact_id = Column(Integer, ForeignKey('users.id'))
    attendees = Column(Integer)
    notes = Column(String)
    
    # Relations
    contract = relationship("Contract", back_populates="events")
    client = relationship("Client", back_populates="events")
    support_contact = relationship("User", back_populates="events")
    
    
class Department(Base):
    __tablename__ = 'departments'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    departement_name = Column(String) 
    
    # Relations
    users = relationship("User", back_populates="department")
        