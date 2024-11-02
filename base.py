import abc


class APIBackend(abc.ABC):
    def submit_api(msg: str) -> any:
        """Submit the given message to the API, and return an object
        representing the server's response.
        """
        pass
    