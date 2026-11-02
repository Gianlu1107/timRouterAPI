class RouterException(Exception):
    """Base exception for router API errors."""
    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message)
        self.message = message
        self.status_code = status_code

class RouterAuthException(RouterException):
    """Raised when authentication with the router fails."""
    def __init__(self, message: str = "Router authentication failed"):
        super().__init__(message, status_code=401)

class RouterConnectionException(RouterException):
    """Raised when connecting to the router fails."""
    def __init__(self, message: str = "Unable to connect to router"):
        super().__init__(message, status_code=502)

class RouterProtocolException(RouterException):
    """Raised when router returns an unexpected response format."""
    def __init__(self, message: str = "Invalid response protocol from router"):
        super().__init__(message, status_code=502)

class RouterConfigException(RouterException):
    """Raised when applying a configuration to the router fails."""
    def __init__(self, message: str = "Failed to apply router configuration"):
        super().__init__(message, status_code=400)
