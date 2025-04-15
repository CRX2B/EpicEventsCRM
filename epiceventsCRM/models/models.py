from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    """
    Modèle représentant un utilisateur du système.
    
    Attributes:
        id (int): Identifiant unique de l'utilisateur
        fullname (str): Nom complet de l'utilisateur
        email (str): Adresse email unique de l'utilisateur
        password (str): Mot de passe hashé de l'utilisateur
        departement_id (int): ID du département auquel appartient l'utilisateur
        
    Relationships:
        department: Relation avec le département de l'utilisateur
        clients: Liste des clients gérés par l'utilisateur
        contracts: Liste des contrats gérés par l'utilisateur
        events: Liste des événements supportés par l'utilisateur
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    fullname = Column(String)
    email = Column(String, unique=True)
    password = Column(String)
    departement_id = Column(Integer, ForeignKey("departments.id"))

    # Relations
    department = relationship("Department", back_populates="users")
    clients = relationship("Client", back_populates="sales_contact")
    contracts = relationship("Contract", back_populates="sales_contact")
    events = relationship("Event", back_populates="support_contact")

    def __repr__(self):
        return f"User(fullname='{self.fullname}', email='{self.email}')"


class Client(Base):
    """
    Modèle représentant un client du système.
    
    Attributes:
        id (int): Identifiant unique du client
        fullname (str): Nom complet du client
        email (str): Adresse email unique du client
        phone_number (int): Numéro de téléphone du client
        enterprise (str): Nom de l'entreprise du client
        create_date (DateTime): Date de création du client
        update_date (DateTime): Date de dernière mise à jour
        sales_contact_id (int): ID du commercial responsable
        
    Relationships:
        sales_contact: Relation avec le commercial responsable
        contracts: Liste des contrats du client
        events: Liste des événements du client
    """
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, autoincrement=True)
    fullname = Column(String)
    email = Column(String, unique=True)
    phone_number = Column(Integer)
    enterprise = Column(String)
    create_date = Column(DateTime)
    update_date = Column(DateTime)
    sales_contact_id = Column(Integer, ForeignKey("users.id"))

    # Relations
    sales_contact = relationship("User", back_populates="clients")
    contracts = relationship("Contract", back_populates="client")
    events = relationship("Event", back_populates="client")

    def __repr__(self):
        return f"Client(fullname='{self.fullname})"


class Contract(Base):
    """
    Modèle représentant un contrat dans le système.
    
    Attributes:
        id (int): Identifiant unique du contrat
        client_id (int): ID du client associé
        amount (float): Montant total du contrat
        remaining_amount (float): Montant restant à payer
        create_date (DateTime): Date de création du contrat
        status (bool): Statut du contrat (signé ou non)
        sales_contact_id (int): ID du commercial responsable
        
    Relationships:
        client: Relation avec le client
        sales_contact: Relation avec le commercial responsable
        events: Liste des événements associés au contrat
    """
    __tablename__ = "contracts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(Integer, ForeignKey("clients.id"))
    amount = Column(Float)
    remaining_amount = Column(Float)
    create_date = Column(DateTime)
    status = Column(Boolean)
    sales_contact_id = Column(Integer, ForeignKey("users.id"))

    # Relations
    client = relationship("Client", back_populates="contracts")
    sales_contact = relationship("User", back_populates="contracts")
    events = relationship("Event", back_populates="contract")


class Event(Base):
    """
    Modèle représentant un événement dans le système.
    
    Attributes:
        id (int): Identifiant unique de l'événement
        name (str): Nom de l'événement
        contract_id (int): ID du contrat associé
        client_id (int): ID du client associé
        start_event (DateTime): Date et heure de début
        end_event (DateTime): Date et heure de fin
        location (str): Lieu de l'événement
        support_contact_id (int): ID du contact support
        attendees (int): Nombre de participants
        notes (str): Notes sur l'événement
        
    Relationships:
        contract: Relation avec le contrat associé
        client: Relation avec le client
        support_contact: Relation avec le contact support
    """
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    contract_id = Column(Integer, ForeignKey("contracts.id"))
    client_id = Column(Integer, ForeignKey("clients.id"))
    start_event = Column(DateTime)
    end_event = Column(DateTime)
    location = Column(String)
    support_contact_id = Column(Integer, ForeignKey("users.id"))
    attendees = Column(Integer)
    notes = Column(String)

    # Relations
    contract = relationship("Contract", back_populates="events")
    client = relationship("Client", back_populates="events")
    support_contact = relationship("User", back_populates="events")

    def get_client_info(self):
        """Récupère les informations du client associé à l'événement"""
        if self.client:
            return {
                "name": self.client.fullname,
                "email": self.client.email,
                "phone": self.client.phone_number,
            }
        return None


class Department(Base):
    """
    Modèle représentant un département dans le système.
    
    Attributes:
        id (int): Identifiant unique du département
        departement_name (str): Nom du département
        
    Relationships:
        users: Liste des utilisateurs appartenant au département
    """
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    departement_name = Column(String)

    # Relations
    users = relationship("User", back_populates="department")
