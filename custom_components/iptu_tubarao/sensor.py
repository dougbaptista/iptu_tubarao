"""Sensor que consulta se há débitos no IPTU Tubarão e captura o nome do proprietário."""
import logging
import httpx
from bs4 import BeautifulSoup

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.entity import DeviceInfo, CoordinatorEntity, DataUpdateCoordinator
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from . import DOMAIN

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = "IPTU Tubarão"


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Configura os sensores a partir de uma config_entry."""
    cpf = entry.data.get("cpf").replace(".", "").replace("-", "")

    coordinator = IptuTubaraoCoordinator(hass, cpf=cpf)
    await coordinator.async_config_entry_first_refresh()

    async_add_entities([
        IptuTubaraoDebitoSensor(coordinator, cpf),
        IptuTubaraoNomeSensor(coordinator),
    ], update_before_add=True)


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

        # Captura o nome do proprietário
        nome_element = soup.find("div", class_="h5 mb-0 font-weight-bold text-gray-800")
        nome_proprietario = nome_element.get_text(strip=True).split("-")[1].strip() if nome_element else "Desconhecido"

        return {
            "tem_debitos": tem_debitos,
            "mensagem": mensagem,
            "proprietario": nome_proprietario,
        }


class IptuTubaraoDebitoSensor(CoordinatorEntity, SensorEntity):
    """Sensor que informa se há débitos."""

    def __init__(self, coordinator: IptuTubaraoCoordinator, cpf: str):
        """Inicializa a entidade."""
        super().__init__(coordinator)
        self._cpf = cpf
        self._attr_unique_id = f"iptu_tubarao_{cpf}"
        self._attr_icon = "mdi:alert-circle-check"

    @property
    def name(self):
        """Nome do sensor."""
        return f"IPTU Tubarão {self._cpf}"

    @property
    def native_value(self):
        """Retorna o estado do sensor."""
        data = self.coordinator.data
        return "com_debito" if data.get("tem_debitos") else "sem_debito"

    @property
    def extra_state_attributes(self):
        """Retorna detalhes extras, como a mensagem."""
        data = self.coordinator.data
        return {"mensagem": data.get("mensagem", "")}


class IptuTubaraoNomeSensor(CoordinatorEntity, SensorEntity):
    """Sensor que informa o nome do proprietário."""

    def __init__(self, coordinator: IptuTubaraoCoordinator):
        """Inicializa a entidade."""
        super().__init__(coordinator)
        self._attr_unique_id = "iptu_tubarao_nome"
        self._attr_icon = "mdi:account"

    @property
    def name(self):
        """Nome do sensor."""
        return "IPTU Tubarão Nome"

    @property
    def native_value(self):
        """Retorna o nome do proprietário."""
        data = self.coordinator.data
        return data.get("proprietario", "Desconhecido")
