class DomainError(Exception):
    """Base for expected business-rule failures mapped to HTTP status codes."""


class NotFoundError(DomainError):
    pass


class SlotUnavailableError(DomainError):
    pass


class InvalidTransitionError(DomainError):
    pass
