"""Sensor que consulta se há débitos no IPTU Tubarão."""
import logging
import httpx
from bs4 import BeautifulSoup

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass
)
from homeassistant.const import CONF_NAME
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from . import DOMAIN

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = "IPTU Tubarão"


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Configura o sensor a partir de uma config_entry."""
    cpf = entry.data.get("cpf")
    name = entry.data.get(CONF_NAME, DEFAULT_NAME)

    coordinator = IptuTubaraoCoordinator(hass, cpf=cpf)
    # Faz update inicial
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
            update_interval=None,  # Configure o intervalo de atualização se quiser, ex: timedelta(hours=24)
        )
        self._cpf = cpf
        self._session = httpx.AsyncClient(verify=True)

    async def _async_update_data(self):
        """Método chamado periodicamente para buscar dados."""
        return await self._fetch_debitos()

    async def _fetch_debitos(self):
        """
        Faz POST do CPF e coleta se há debitos.
        Retorna algo como: {'tem_debitos': True/False, 'mensagem': "..."}
        """
        url = "https://tubarao-sc.prefeituramoderna.com.br/meuiptu/index.php?cidade=tubarao"

        # 1) Faz GET inicial (carrega a página, possivelmente para pegar cookies).
        try:
            r_get = await self._session.get(url, timeout=30)
            r_get.raise_for_status()
        except Exception as err:
            _LOGGER.error("Erro ao acessar URL inicial: %s", err)
            raise

        # 2) Monta os dados do formulário.  
        #   De acordo com o site, o form possui campos "documento" e "inscricao" etc.  
        #   No seu HTML, há: <input type="text" id="documento" name="documento">
        #   e <input type="text" id="inscricao" name="inscricao">
        #   Mas se o usuário só tem CPF, podemos mandar "inscricao" vazio ou -1.
        form_data = {
            "documento": self._cpf,
            "inscricao": "",
            "st_menu": "1",
        }

        # 3) Faz POST com os dados do formulário.
        try:
            r_post = await self._session.post(url, data=form_data, timeout=30)
            r_post.raise_for_status()
        except Exception as err:
            _LOGGER.error("Erro ao enviar CPF: %s", err)
            raise

        # 4) Agora precisamos analisar se a resposta indica "Não foram localizados débitos" ou se retornou algo
        soup = BeautifulSoup(r_post.text, "html.parser")

        # Exemplo de checagem textual simples:
        if "Não foram localizados débitos" in soup.get_text():
            return {
                "tem_debitos": False,
                "mensagem": "Nenhum débito encontrado"
            }

        # Podemos também procurar a div/classe que mostra que existe algum débito.
        # Se não achar, assumimos que não tem
        # Exemplo rápido: ver se existe a tabela de débitos
        div_nao_localizado = soup.find_all(string="Não foram localizados débitos com as informações selecionadas.")
        if div_nao_localizado:
            return {
                "tem_debitos": False,
                "mensagem": "Nenhum débito encontrado"
            }

        # Caso contrário, assume que achou algo
        return {
            "tem_debitos": True,
            "mensagem": "Foi localizado algum débito!"
        }


class IptuTubaraoSensor(CoordinatorEntity, SensorEntity):
    """Entidade Sensor que informa se há débitos ou não."""

    _attr_has_entity_name = True  # Usa o "name" do domain device
    _attr_icon = "mdi:home-alert"

    def __init__(self, coordinator: IptuTubaraoCoordinator, name: str, cpf: str):
        """Inicializa a entidade."""
        super().__init__(coordinator)
        self._cpf = cpf
        self._name = name

        # Se quiser criar unique_id combinando CPF
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
        """Retorna detalhes extras, como a mensagem."""
        if not self.coordinator.data:
            return {}
        return {
            "mensagem": self.coordinator.data.get("mensagem", "")
        }

    @property
    def device_info(self) -> DeviceInfo:
        """Opcional: agrupar como 'dispositivo' no HA."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._cpf)},
            name=f"IPTU Tubarão - CPF {self._cpf}",
            manufacturer="Prefeitura de Tubarão",
            model="Consulta IPTU Online",
        )

    async def async_update(self):
        """Para forçar update quando chamado manualmente."""
        await self.coordinator.async_request_refresh()
