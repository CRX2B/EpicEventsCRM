from typing import Dict, List, Optional, Type, TypeVar, Generic
from sqlalchemy.orm import Session
from datetime import datetime
from epiceventsCRM.models.models import Client, Contract, Event, User

ModelType = TypeVar("ModelType")


class MockBaseDAO(Generic[ModelType]):
    """Classe de base pour les mocks de DAO"""

    def __init__(self, model: Type[ModelType]):
        """
        Initialise le mock DAO avec le modèle spécifié.

        Args:
            model (Type[ModelType]): Le modèle SQLAlchemy à utiliser
        """
        self.model = model
        self._data: Dict[int, ModelType] = {}
        self.next_id = 1

    def get(self, db: Session, id: int) -> Optional[ModelType]:
        """Récupère une entité par son ID"""
        return self._data.get(id)

    def get_all(self, db: Session, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """Récupère toutes les entités avec pagination"""
        return list(self._data.values())[skip : skip + limit]

    def create(self, db: Session, obj_in: dict) -> ModelType:
        """Crée une nouvelle entité"""
        db_obj = self.model(**obj_in)
        db_obj.id = self.next_id
        self.next_id += 1
        self._data[db_obj.id] = db_obj
        return db_obj

    def update(self, db: Session, db_obj: ModelType, obj_in: dict) -> ModelType:
        """Met à jour une entité"""
        for key, value in obj_in.items():
            setattr(db_obj, key, value)
        return db_obj

    def delete(self, db: Session, id: int) -> bool:
        """Supprime une entité"""
        if id in self._data:
            del self._data[id]
            return True
        return False


class MockClientDAO(MockBaseDAO):
    """Mock du ClientDAO pour les tests"""

    def __init__(self):
        super().__init__(Client)

    def create(self, db: Session, client_data: dict) -> ModelType:
        now = datetime.now()
        client = self.model(
            id=self.next_id,
            fullname=client_data.get("fullname"),
            email=client_data.get("email"),
            phone_number=client_data.get("phone_number"),
            enterprise=client_data.get("enterprise"),
            create_date=now,
            update_date=now,
            sales_contact_id=client_data.get("sales_contact_id")
        )
        self.next_id += 1
        self._data[client.id] = client
        return client

    def update(self, db: Session, db_obj: ModelType, obj_in: dict) -> ModelType:
        obj_in["update_date"] = datetime.now()
        return super().update(db, db_obj, obj_in)

    def get_by_email(self, db: Session, email: str) -> Optional[ModelType]:
        return next((client for client in self._data.values() if client.email == email), None)

    def get_by_sales_contact(self, db: Session, sales_contact_id: int) -> List[ModelType]:
        return [client for client in self._data.values() if client.sales_contact_id == sales_contact_id]


class MockContractDAO(MockBaseDAO):
    """Mock du ContractDAO pour les tests"""

    def __init__(self, client_dao=None):
        super().__init__(Contract)
        self.client_dao = client_dao or MockClientDAO()

    def create(self, db: Session, *args, **kwargs) -> ModelType:
        # Gérer les deux cas : args[0] est un dict ou kwargs contient les arguments
        if args and isinstance(args[0], dict):
            obj_in = args[0]
        else:
            obj_in = kwargs

        # Si remaining_amount n'est pas spécifié, on le met égal à amount
        if "remaining_amount" not in obj_in and "amount" in obj_in:
            obj_in["remaining_amount"] = obj_in["amount"]
            
        # Récupérer le client pour obtenir son sales_contact_id
        client = self.client_dao.get(db, obj_in.get("client_id"))
        sales_contact_id = client.sales_contact_id if client else None
            
        contract = self.model(
            id=self.next_id,
            client_id=obj_in.get("client_id"),
            amount=obj_in.get("amount"),
            remaining_amount=obj_in.get("remaining_amount"),
            status=obj_in.get("status", False),
            sales_contact_id=sales_contact_id,
            create_date=datetime.now()
        )
        self.next_id += 1
        self._data[contract.id] = contract
        return contract

    def get_by_client(self, db: Session, client_id: int) -> List[ModelType]:
        return [contract for contract in self._data.values() if contract.client_id == client_id]

    def get_by_commercial(self, db: Session, commercial_id: int) -> List[ModelType]:
        return [contract for contract in self._data.values() if contract.sales_contact_id == commercial_id]

    def update_status(self, db: Session, contract_id: int, status: bool) -> Optional[ModelType]:
        contract = self.get(db, contract_id)
        if contract:
            contract.status = status
            return contract
        return None

    def update_remaining_amount(self, db: Session, contract_id: int, amount: float) -> Optional[ModelType]:
        contract = self.get(db, contract_id)
        if contract:
            contract.remaining_amount = amount
            return contract
        return None


class MockEventDAO(MockBaseDAO):
    """Mock du EventDAO pour les tests"""

    def __init__(self):
        super().__init__(Event)

    def create(self, db: Session, *args, **kwargs) -> ModelType:
        # Gérer les deux cas : args[0] est un dict ou kwargs contient les arguments
        if args and isinstance(args[0], dict):
            obj_in = args[0]
        else:
            obj_in = kwargs

        # Vérification des champs obligatoires
        if not all(key in obj_in for key in ["name", "start_event", "end_event"]):
            raise ValueError("Les champs name, start_event et end_event sont obligatoires")
            
        event = self.model(
            id=self.next_id,
            name=obj_in["name"],
            contract_id=obj_in.get("contract_id"),
            client_id=obj_in.get("client_id"),
            start_event=obj_in["start_event"],
            end_event=obj_in["end_event"],
            location=obj_in.get("location"),
            support_contact_id=obj_in.get("support_contact_id"),
            attendees=obj_in.get("attendees", 0),
            notes=obj_in.get("notes", "")
        )
        self.next_id += 1
        self._data[event.id] = event
        return event

    def create_event(self, db: Session, *args, **kwargs) -> ModelType:
        """Alias pour la méthode create pour la compatibilité avec les tests"""
        return self.create(db, *args, **kwargs)

    def get_by_client(self, db: Session, client_id: int) -> List[ModelType]:
        return [event for event in self._data.values() if event.client_id == client_id]

    def get_by_contract(self, db: Session, contract_id: int) -> List[ModelType]:
        return [event for event in self._data.values() if event.contract_id == contract_id]

    def get_by_support(self, db: Session, support_id: int) -> List[ModelType]:
        return [event for event in self._data.values() if event.support_contact_id == support_id]

    def get_by_commercial(self, db: Session, commercial_id: int) -> List[ModelType]:
        # Cette méthode nécessite d'accéder au contract.sales_contact_id
        # On doit donc s'assurer que le contract existe
        return [
            event for event in self._data.values() 
            if event.contract and event.contract.sales_contact_id == commercial_id
        ]


class MockUserDAO(MockBaseDAO):
    """Mock du UserDAO pour les tests"""

    def __init__(self):
        super().__init__(User)

    def get_by_email(self, db: Session, email: str) -> Optional[ModelType]:
        return next((user for user in self._data.values() if user.email == email), None)

    def get_by_department(self, db: Session, department_id: int) -> List[ModelType]:
        return [user for user in self._data.values() if user.departement_id == department_id]

    def create(self, db: Session, obj_in: dict) -> ModelType:
        """Crée un nouvel utilisateur"""
        user = self.model(
            fullname=obj_in["fullname"],
            email=obj_in["email"],
            password=obj_in["password"],
            departement_id=obj_in["departement_id"],
        )
        user.id = self.next_id
        self.next_id += 1
        self._data[user.id] = user
        return user
