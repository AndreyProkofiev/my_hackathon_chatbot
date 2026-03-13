from bot_api.endpoints.ask import router as ask
from bot_api.endpoints.health import router as health
from bot_api.endpoints.process_message import router as process_message


list_of_routes = [ask, health, process_message]

__all__ = ["list_of_routes"]
