"""Inicialização do componente IPTU Tubarão."""
import logging
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

DOMAIN = "iptu_tubarao"
_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config: dict):
    """Configuração inicial via configuration.yaml (se usar)."""
    _LOGGER.info("async_setup chamado")
    # Se for usar APENAS config_flow, pode deixar isso vazio.
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Configuração feita quando o usuário adiciona via UI (config flow)."""
    _LOGGER.info(f"Configurando entrada: {entry.data}")

    # Adicione as entidades (sensores) do sensor.py
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "sensor")
    )
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Descarrega o componente quando removido via UI."""
    _LOGGER.info(f"Descarregando entrada: {entry.data}")
    await hass.config_entries.async_forward_entry_unload(entry, "sensor")
    return True
