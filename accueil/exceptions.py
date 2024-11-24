


class AccueilException(Exception):
    message = ""
    status = ""
    pass


# -- XMLRPC
class TooManyRegistrationsSet(AccueilException):
    message = """Un membre ne peut pas s'inscrire à plus de 5 créneaux par 28 jours."""
    status = 500
    def __init__(self) -> None:
        super().__init__(self.message)

class DuplicateRegistration(AccueilException):
    message = """Ce membre est déjà inscrit sur ce créneau."""
    status = 500
    def __init__(self) -> None:
        super().__init__(self.message)


class UnknownXmlrcpError(AccueilException):
    message = """Une erreur s'est produite."""
    status = 500
    def __init__(self) -> None:
        super().__init__(self.message)

class NoMoreSeatsAvailable(AccueilException):
    message = """Service Complet."""
    status = 500
    def __init__(self) -> None:
        super().__init__(self.message)

class CannotRegisterDuringLeavePeriod(AccueilException):
    message = """Inscription aux services se déroulant pendant les congés d'un membre est impossible."""
    status = 500
    def __init__(self) -> None:
        super().__init__(self.message)

class UnknownSocketError(AccueilException):
    message = """Une erreur s'est produite."""
    status = 500
    def __init__(self) -> None:
        super().__init__(self.message)


# -- MAIL
class TooManyReceivers(AccueilException):
    message = """Ne peut pas envoyer un mail à autant de personnes. Utilisez send_group à la place."""
    status = 500
    def __init__(self) -> None:
        super().__init__(self.message)

class UnknownSender(AccueilException):
    message = """Envoyeur inconnu."""
    status = 500
    def __init__(self) -> None:
        super().__init__(self.message)

class UnknownMailTemplate(AccueilException):
    message = """Template de mail Inconnu."""
    status = 500
    def __init__(self) -> None:
        super().__init__(self.message)


class UnknownShift(AccueilException):
    message = """Shift Unknown"""
    status = 500
    def __init__(self) -> None:
        super().__init__(self.message)
