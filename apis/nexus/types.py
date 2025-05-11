import datetime

base_message = "(error code {code}): {message}"

class NexusApiError(BaseException):
    """Underlying class representing Nexus API errors"""
    def __init__(self, m):
        super().__init__(m)

class Conflict(NexusApiError):
    def __init__(self, code, message):
        super().__init__(base_message.format(code=code, message=message))
class BadRequest(NexusApiError):
    def __init__(self, code, message):
        super().__init__(base_message.format(code=code, message=message))
class Unauthorized(NexusApiError):
    def __init__(self, code, message):
        super().__init__(base_message.format(code=code, message=message))
class Forbidden(NexusApiError):
    def __init__(self, code, message):
        super().__init__(base_message.format(code=code, message=message))
class NotFound(NexusApiError):
    def __init__(self, code, message):
        super().__init__(base_message.format(code=code, message=message))
class MethodNotAllowed(NexusApiError):
    def __init__(self, code, message):
        super().__init__(base_message.format(code=code, message=message))
class PayloadTooLarge(NexusApiError):
    def __init__(self, code, message):
        super().__init__(base_message.format(code=code, message=message))
class InternalServerError(NexusApiError):
    def __init__(self, code, message):
        super().__init__(base_message.format(code=code, message=message))

class RobloxAccount:
    def __init__(self, account_data):
        self.id: int = int(account_data.pop("id"))

class Date:
    def __init__(self, iso: str):
        self._iso = iso
        self._datetime: datetime.datetime = datetime.datetime.fromisoformat(iso)
        self._epoch: float = self._datetime.timestamp()

    def __repr__(self):
        return self.iso
    
    @property
    def iso(self):
        return self._iso
    
    @property
    def datetime(self):
        return self._datetime
    
    @property
    def timestamp(self):
        return self._epoch

class Account:
    def __init__(self, account_data: dict):
        self.discord_id: int = int(account_data.pop("discord")) # The Discord account ID to identify the Nexus account 
        self.created_at: Date = Date(account_data.pop("createdAt")) # When the Nexus account was first created
        self.roblox_accounts: RobloxAccount = [RobloxAccount(d) for d in account_data["roblox"]] # Linked Roblox accounts

class SubjectType:
    @classmethod
    def Roblox(cls):
        return 0
    
    @classmethod
    def Discord(cls):
        return 1
    
class Session:
    def __init__(self, url: str, expires_at: str):
        self.url = url
        self.expiration = Date(expires_at)
    
    @property
    def is_expired(self):
        return datetime.datetime.now().timestamp() > self.expiration.timestamp