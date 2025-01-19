"""Sensor que consulta se há débitos no IPTU Tubarão."""
import logging
import httpx
from bs4 import BeautifulSoup

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from . import DOMAIN

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = "IPTU Tubarão"


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Configura o sensor a partir de uma config_entry."""
    cpf = entry.data.get("cpf").replace(".", "").replace("-", "")
    name = entry.data.get("name", DEFAULT_NAME)

    coordinator = IptuTubaraoCoordinator(hass, cpf=cpf)
    await coordinator.async_config_entry_first_refresh()

    async_add_entities([IptuTubaraoSensor(coordinator, name, cpf)], update_before_add=True)


class IptuTubaraoCoordinator(DataUpdateCoordinator):
    """Coordenador que faz a requisição ao site periodicamente."""

    def __init__(self, hass: HomeAssistant, cpf: str):
        """Inicializa."""
        super().__init__(
            hass,
            _LOGGER,
            name="iptu_tubarao_coordinator",
        )
        self._cpf = cpf
        self._session = httpx.AsyncClient(verify=True)

    async def _async_update_data(self):
        """Busca os dados de débitos e nome do proprietário."""
        return await self._fetch_debitos()

    async def _fetch_debitos(self):
        """
        Faz POST do CPF e coleta se há débitos e o nome do proprietário.
        """
        url = "https://tubarao-sc.prefeituramoderna.com.br/meuiptu/index.php?cidade=tubarao"

        try:
            r_get = await self._session.get(url, timeout=30)
            r_get.raise_for_status()
        except Exception as err:
            _LOGGER.error("Erro ao acessar URL inicial: %s", err)
            raise

        form_data = {
            "documento": self._cpf,
            "inscricao": "",
            "st_menu": "1",
        }

        try:
            r_post = await self._session.post(url, data=form_data, timeout=30)
            r_post.raise_for_status()
        except Exception as err:
            _LOGGER.error("Erro ao enviar CPF: %s", err)
            raise

        soup = BeautifulSoup(r_post.text, "html.parser")

        tem_debitos = "Não foram localizados débitos" not in soup.get_text()
        mensagem = "Nenhum débito encontrado" if not tem_debitos else "Foi localizado algum débito!"

        proprietario = soup.find("span", id="proprietario")
        proprietario_nome = proprietario.get_text(strip=True) if proprietario else "Não identificado"

        return {
            "tem_debitos": tem_debitos,
            "mensagem": mensagem,
            "proprietario": proprietario_nome,
        }


class IptuTubaraoSensor(CoordinatorEntity, SensorEntity):
    """Entidade Sensor que informa se há débitos ou não."""

    _attr_icon = "mdi:home-alert"

    def __init__(self, coordinator: IptuTubaraoCoordinator, name: str, cpf: str):
        """Inicializa a entidade."""
        super().__init__(coordinator)
        self._cpf = cpf
        self._name = name
        self._attr_unique_id = f"iptu_tubarao_{cpf}"

    @property
    def name(self):
        """Nome do sensor."""
        return self._name

    @property
    def native_value(self):
        """Retorna o estado do sensor: 'com_debito' ou 'sem_debito'."""
        data = self.coordinator.data
        if not data:
            return None
        return "com_debito" if data.get("tem_debitos") else "sem_debito"

    @property
    def extra_state_attributes(self):
        """Retorna detalhes extras, como a mensagem e o nome do proprietário."""
        if not self.coordinator.data:
            return {}
        return {
            "mensagem": self.coordinator.data.get("mensagem", ""),
            "proprietario": self.coordinator.data.get("proprietario", "Não identificado"),
        }

    @property
    def device_info(self) -> DeviceInfo:
        """Agrupa como dispositivo no Home Assistant."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._cpf)},
            name=f"IPTU Tubarão - CPF {self._cpf}",
            manufacturer="Prefeitura de Tubarão",
            model="Consulta IPTU Online",
        )
