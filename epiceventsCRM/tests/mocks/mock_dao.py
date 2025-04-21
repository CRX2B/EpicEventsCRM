from typing import Dict, List, Optional, Type, TypeVar, Generic
from sqlalchemy.orm import Session
from datetime import datetime
from unittest.mock import Mock
from epiceventsCRM.models.models import Client, Contract, Event, User, Department

ModelType = TypeVar("ModelType")


class MockBaseDAO(Generic[ModelType]):
    """Classe de base pour les mocks de DAO avec suivi des appels"""

    def __init__(self, model: Type[ModelType]):
        """
        Initialise le mock DAO avec le modèle spécifié et enveloppe les méthodes avec Mock.

        Args:
            model (Type[ModelType]): Le modèle SQLAlchemy à utiliser
        """
        self.model = model
        self._data: Dict[int, ModelType] = {}
        self.next_id = 1

        self._original_get = self._get_impl
        self._original_get_all = self._get_all_impl
        self._original_create = self._create_impl
        self._original_update = self._update_impl
        self._original_delete = self._delete_impl

        self.get = Mock(side_effect=self._original_get)
        self.get_all = Mock(side_effect=self._original_get_all)
        self.create = Mock(side_effect=self._original_create)
        self.update = Mock(side_effect=self._original_update)
        self.delete = Mock(side_effect=self._original_delete)

    def _get_impl(self, db: Session, id: int) -> Optional[ModelType]:
        """Récupère une entité par son ID"""
        return self._data.get(id)

    def _get_all_impl(self, db: Session, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """Récupère toutes les entités avec pagination"""
        all_items = list(self._data.values())
        return all_items[skip : skip + limit]

    def _create_impl(self, db: Session, *args, **kwargs) -> ModelType:
        """Crée une nouvelle entité. Gère kwargs ou un dict dans args[0]."""
        if args and isinstance(args[0], dict):
            obj_in = args[0]
        else:
            obj_in = kwargs
        valid_keys = [col.name for col in self.model.__table__.columns]
        filtered_obj_in = {k: v for k, v in obj_in.items() if k in valid_keys}

        db_obj = self.model(**filtered_obj_in)
        if not getattr(db_obj, "id", None):
            db_obj.id = self.next_id
            self.next_id += 1
        if hasattr(db_obj, "create_date") and not getattr(db_obj, "create_date", None):
            db_obj.create_date = datetime.now()
        if hasattr(db_obj, "update_date") and not getattr(db_obj, "update_date", None):
            db_obj.update_date = datetime.now()
        self._data[db_obj.id] = db_obj
        return db_obj

    def _update_impl(self, db: Session, db_obj: ModelType, obj_in: dict) -> ModelType:
        """Met à jour une entité et la stocke dans le mock"""
        valid_keys = [col.name for col in self.model.__table__.columns]
        obj_id = getattr(db_obj, "id", None)
        if obj_id is None:
            return None

        for key, value in obj_in.items():
            if key in valid_keys:
                setattr(db_obj, key, value)
        if hasattr(db_obj, "update_date"):
            db_obj.update_date = datetime.now()

        self._data[obj_id] = db_obj

        return db_obj

    def _delete_impl(self, db: Session, id: int) -> bool:
        """Supprime une entité"""
        if id in self._data:
            del self._data[id]
            return True
        return False

    def reset_mocks(self):
        self._data.clear()
        self.next_id = 1
        self.get.reset_mock()
        self.get_all.reset_mock()
        self.create.reset_mock()
        self.update.reset_mock()
        self.delete.reset_mock()


class MockClientDAO(MockBaseDAO):
    """Mock du ClientDAO pour les tests"""

    def __init__(self):
        super().__init__(Client)

        self._original_create_client = self._create_client_impl
        self.create_client = Mock(side_effect=self._original_create_client)
        self._original_update_client = self._update_client_impl
        self.update_client = Mock(side_effect=self._original_update_client)
        self._original_get_by_email = self._get_by_email_impl
        self.get_by_email = Mock(side_effect=self._original_get_by_email)
        self._original_get_by_sales_contact = self._get_by_sales_contact_impl
        self.get_by_sales_contact = Mock(side_effect=self._original_get_by_sales_contact)
        self._original_update_commercial = self._update_commercial_impl
        self.update_commercial = Mock(side_effect=self._original_update_commercial)

    def _create_client_impl(self, db: Session, client_data: dict) -> ModelType:
        """Implémentation spécifique pour créer un client avec dates."""
        now = datetime.now()
        client_data["create_date"] = now
        client_data["update_date"] = now
        return super()._create_impl(db, client_data)

    def _update_client_impl(self, db: Session, client_id: int, client_data: dict) -> ModelType:
        """Implémentation spécifique pour mettre à jour un client."""
        client_obj = self._get_impl(db, client_id)
        if client_obj:
            return self._update_impl(db, client_obj, client_data)
        return None

    def _get_by_email_impl(self, db: Session, email: str) -> Optional[ModelType]:
        return next((client for client in self._data.values() if client.email == email), None)

    def _get_by_sales_contact_impl(self, db: Session, sales_contact_id: int) -> List[ModelType]:
        return [
            client for client in self._data.values() if client.sales_contact_id == sales_contact_id
        ]

    def _update_commercial_impl(
        self, db: Session, client: Client, commercial_id: int
    ) -> Optional[Client]:
        """Implémentation spécifique pour mettre à jour le commercial d'un client."""
        if client and getattr(client, "id", None) is not None:
            client.sales_contact_id = commercial_id
            client.update_date = datetime.now()
            self._data[client.id] = client
            return client
        return None

    def reset_mocks(self):
        super().reset_mocks()
        self.create_client.reset_mock()
        self.update_client.reset_mock()
        self.get_by_email.reset_mock()
        self.get_by_sales_contact.reset_mock()
        self.update_commercial.reset_mock()


class MockContractDAO(MockBaseDAO):
    """Mock du ContractDAO pour les tests"""

    def __init__(self, client_dao=None):
        super().__init__(Contract)
        self.client_dao = client_dao or MockClientDAO()
        self._original_create = self._create_impl
        self.create = Mock(side_effect=self._original_create)

        self._original_get_by_client = self._get_by_client_impl
        self.get_by_client = Mock(side_effect=self._original_get_by_client)
        self._original_get_by_commercial = self._get_by_commercial_impl
        self.get_by_commercial = Mock(side_effect=self._original_get_by_commercial)
        self._original_update_status = self._update_status_impl
        self.update_status = Mock(side_effect=self._original_update_status)
        self._original_update_remaining_amount = self._update_remaining_amount_impl
        self.update_remaining_amount = Mock(side_effect=self._original_update_remaining_amount)

        self._original_create_contract = self._create_contract_impl
        self.create_contract = Mock(side_effect=self._original_create_contract)

    def _create_impl(self, db: Session, *args, **kwargs) -> ModelType:
        if args and isinstance(args[0], dict):
            obj_in = args[0]
        else:
            obj_in = kwargs

        if "remaining_amount" not in obj_in and "amount" in obj_in:
            obj_in["remaining_amount"] = obj_in["amount"]

        client = self.client_dao.get(db, obj_in.get("client_id"))
        sales_contact_id = client.sales_contact_id if client else None
        obj_in["sales_contact_id"] = sales_contact_id

        return super()._create_impl(db, obj_in)

    def _create_contract_impl(
        self,
        db: Session,
        client_id: int,
        amount: float,
        sales_contact_id: int,
        status: bool = False,
    ) -> ModelType:
        """Implémentation spécifique pour créer un contrat via create_contract."""
        contract_data = {
            "client_id": client_id,
            "amount": amount,
            "remaining_amount": amount,
            "create_date": datetime.now(),
            "status": status,
            "sales_contact_id": sales_contact_id,
        }
        return super()._create_impl(db, contract_data)

    def _get_by_client_impl(self, db: Session, client_id: int) -> List[ModelType]:
        return [contract for contract in self._data.values() if contract.client_id == client_id]

    def _get_by_commercial_impl(self, db: Session, commercial_id: int) -> List[ModelType]:
        return [
            contract
            for contract in self._data.values()
            if contract.sales_contact_id == commercial_id
        ]

    def _update_status_impl(
        self, db: Session, contract_id: int, status: bool
    ) -> Optional[ModelType]:
        contract = self._get_impl(db, contract_id)
        if contract:
            return self.update(db, contract, {"status": status})
        return None

    def _update_remaining_amount_impl(
        self, db: Session, contract_id: int, amount: float
    ) -> Optional[ModelType]:
        contract = self._get_impl(db, contract_id)
        if contract:
            return self.update(db, contract, {"remaining_amount": amount})
        return None

    def reset_mocks(self):
        super().reset_mocks()
        self.get_by_client.reset_mock()
        self.get_by_commercial.reset_mock()
        self.update_status.reset_mock()
        self.update_remaining_amount.reset_mock()
        self.create_contract.reset_mock()


class MockEventDAO(MockBaseDAO):
    """Mock du EventDAO pour les tests"""

    def __init__(self):
        super().__init__(Event)
        self._original_create = self._create_impl
        self.create = Mock(side_effect=self._original_create)
        self._original_create_event = self._create_event_impl
        self.create_event = Mock(side_effect=self._original_create_event)

        self._original_get_by_client = self._get_by_client_impl
        self.get_by_client = Mock(side_effect=self._original_get_by_client)
        self._original_get_by_contract = self._get_by_contract_impl
        self.get_by_contract = Mock(side_effect=self._original_get_by_contract)
        self._original_get_by_support = self._get_by_support_impl
        self.get_by_support = Mock(side_effect=self._original_get_by_support)
        self._original_get_by_commercial = self._get_by_commercial_impl
        self.get_by_commercial = Mock(side_effect=self._original_get_by_commercial)
        self._original_assign_support_contact = self._assign_support_contact_impl
        self.assign_support_contact = Mock(side_effect=self._original_assign_support_contact)
        self._original_update_notes = self._update_notes_impl
        self.update_notes = Mock(side_effect=self._original_update_notes)
        self._original_update_support = self._update_support_impl
        self.update_support = Mock(side_effect=self._original_update_support)

    def _create_impl(self, db: Session, *args, **kwargs) -> ModelType:
        if args and isinstance(args[0], dict):
            obj_in = args[0]
        else:
            obj_in = kwargs

        if not all(key in obj_in for key in ["name", "start_event", "end_event"]):
            return None

        return super()._create_impl(db, obj_in)

    def _create_event_impl(self, db: Session, *args, **kwargs) -> ModelType:
        """Alias pour la méthode create pour la compatibilité avec les tests"""
        return self._create_impl(db, *args, **kwargs)

    def _get_by_client_impl(self, db: Session, client_id: int) -> List[ModelType]:
        return [event for event in self._data.values() if event.client_id == client_id]

    def _get_by_contract_impl(self, db: Session, contract_id: int) -> List[ModelType]:
        return [event for event in self._data.values() if event.contract_id == contract_id]

    def _get_by_support_impl(self, db: Session, support_id: int) -> List[ModelType]:
        return [event for event in self._data.values() if event.support_contact_id == support_id]

    def _get_by_commercial_impl(self, db: Session, commercial_id: int) -> List[ModelType]:
        return []

    def _assign_support_contact_impl(
        self, db: Session, event_id: int, support_id: int
    ) -> Optional[ModelType]:
        """Simule l'assignation d'un contact support"""
        event = self._get_impl(db, event_id)
        if event:
            return self.update(db, event, {"support_contact_id": support_id})
        return None

    def _update_notes_impl(self, db: Session, event_id: int, notes: str) -> Optional[ModelType]:
        """Simule la mise à jour des notes"""
        event = self._get_impl(db, event_id)
        if event:
            return self.update(db, event, {"notes": notes})
        return None

    def _update_support_impl(
        self, db: Session, event_id: int, support_contact_id: int
    ) -> Optional[Event]:
        """Implémentation mock pour mettre à jour le contact support."""
        event = self._get_impl(db, event_id)
        if event:
            event.support_contact_id = support_contact_id
            event.update_date = datetime.now()
            self._data[event_id] = event
            return event
        return None

    def reset_mocks(self):
        super().reset_mocks()
        self.create_event.reset_mock()
        self.get_by_client.reset_mock()
        self.get_by_contract.reset_mock()
        self.get_by_support.reset_mock()
        self.get_by_commercial.reset_mock()
        self.assign_support_contact.reset_mock()
        self.update_notes.reset_mock()
        self.update_support.reset_mock()


class MockDepartmentDAO(MockBaseDAO):
    """Mock du DepartmentDAO pour les tests"""

    def __init__(self):
        super().__init__(Department)


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
