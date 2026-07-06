import pytest

from app.errors import InvalidTransitionError
from app.state_machine import validate_transition


def test_confirmed_can_be_cancelled():
    validate_transition("confirmed", "cancelled")


def test_confirmed_can_be_completed():
    validate_transition("confirmed", "completed")


@pytest.mark.parametrize(
    "current,target",
    [
        ("cancelled", "completed"),
        ("completed", "cancelled"),
        ("cancelled", "confirmed"),
        ("confirmed", "confirmed"),
    ],
)
def test_invalid_transitions_rejected(current, target):
    with pytest.raises(InvalidTransitionError):
        validate_transition(current, target)
