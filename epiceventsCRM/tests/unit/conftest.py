import pytest
from epiceventsCRM.tests.mocks.mock_controllers import MockAuthController


@pytest.fixture
def mock_auth_controller_fixture():
    return MockAuthController()
