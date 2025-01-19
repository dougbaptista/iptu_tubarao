"""Inicialização do componente IPTU Tubarão."""
import logging

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

DOMAIN = "iptu_tubarao"
_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict):
    """Configuração inicial via configuration.yaml (se usar)."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Configuração feita quando o usuário adiciona via UI (config flow)."""
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "sensor")
    )
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Descarrega o componente quando removido via UI."""
    await hass.config_entries.async_forward_entry_unload(entry, "sensor")
    return True
