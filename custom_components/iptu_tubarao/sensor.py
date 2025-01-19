"""Sensor que consulta se há débitos no IPTU Tubarão."""
import logging
import httpx
from bs4 import BeautifulSoup

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from . import DOMAIN

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = "IPTU Tubarão"


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Configura os sensores a partir de uma config_entry."""
    cpf = entry.data.get("cpf")

    coordinator = IptuTubaraoCoordinator(hass, cpf=cpf)
    
    # Faz update inicial
    await coordinator.async_config_entry_first_refresh()

    # Sempre cria os sensores básicos
    entities = [
        IptuTubaraoSensorCPF(coordinator, cpf),
        IptuTubaraoSensorNome(coordinator, cpf),
        IptuTubaraoSensorStatus(coordinator, cpf),
    ]

    # Cria sensores adicionais conforme os valores retornados
    entities.extend([
        IptuTubaraoSensorValorTotalSemJuros(coordinator, cpf),
        IptuTubaraoSensorValorTotalTaxaUnica(coordinator, cpf),
        IptuTubaraoSensorValorTotalSemDesconto(coordinator, cpf),
    ])

    async_add_entities(entities, update_before_add=True)


class IptuTubaraoCoordinator(DataUpdateCoordinator):
    """Coordenador que faz a requisição ao site periodicamente."""

    def __init__(self, hass: HomeAssistant, cpf: str):
        """Inicializa."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"iptu_tubarao_coordinator_{cpf}",
        )
        self._cpf = cpf
        self._session = httpx.AsyncClient(verify=True)

    async def _async_update_data(self):
        """Busca os dados de débitos e nome do proprietário."""
        return await self._fetch_debitos()

    async def _fetch_debitos(self):
        """Faz POST do CPF e coleta dados de débitos e o nome do proprietário."""
        url = "https://tubarao-sc.prefeituramoderna.com.br/meuiptu/index.php?cidade=tubarao"

        try:
            await self._session.get(url, timeout=30)
        except Exception as err:
            _LOGGER.error("Erro ao acessar URL inicial: %s", err)
            raise

        form_data = {
            "documento": self._cpf,
            "inscricao": "",
            "st_menu": "1",
        }

        try:
            response = await self._session.post(url, data=form_data, timeout=30)
            response.raise_for_status()
        except Exception as err:
            _LOGGER.error("Erro ao enviar CPF: %s", err)
            raise

        soup = BeautifulSoup(response.text, "html.parser")

        # Localizar os valores conforme o layout atualizado
        try:
            valores_totais_element = soup.find(string="VALORES TOTAIS:").find_next("div")
            valores_totais = float(valores_totais_element.text.strip().replace(".", "").replace(",", ".")) if valores_totais_element else 0

            valor_total_taxa_unica_element = soup.find(string="VALOR TOTAL ÚNICA:").find_next("div")
            valor_total_taxa_unica = float(valor_total_taxa_unica_element.text.strip().replace(".", "").replace(",", ".")) if valor_total_taxa_unica_element else 0

            valor_total_sem_desconto_element = soup.find(string="VALOR SEM DESCONTO:").find_next("div")
            valor_total_sem_desconto = float(valor_total_sem_desconto_element.text.strip().replace(".", "").replace(",", ".")) if valor_total_sem_desconto_element else 0
        except Exception as err:
            _LOGGER.error("Erro ao processar os valores: %s", err)
            valores_totais = valor_total_taxa_unica = valor_total_sem_desconto = 0

        nome_element = soup.select_one("span.mr-2.d-none.d-lg-inline.text-gray-600.small")
        nome_proprietario = nome_element.get_text(strip=True) if nome_element else "Desconhecido"

        return {
            "cpf_formatado": self._formatar_cpf(self._cpf),
            "tem_debitos": valores_totais > 0,
            "mensagem": "Nenhum débito encontrado" if valores_totais == 0 else "Foi localizado algum débito!",
            "proprietario": nome_proprietario,
            "valores_totais": valores_totais,
            "valor_total_taxa_unica": valor_total_taxa_unica,
            "valor_total_sem_desconto": valor_total_sem_desconto,
        }

    @staticmethod
    def _formatar_cpf(cpf: str) -> str:
        """Formata o CPF com pontuações."""
        cpf = cpf.zfill(11)
        return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"


class IptuTubaraoSensorCPF(CoordinatorEntity, SensorEntity):
    """Sensor que exibe o CPF formatado."""
    # Sem alterações.


class IptuTubaraoSensorNome(CoordinatorEntity, SensorEntity):
    """Sensor que exibe o nome do proprietário."""
    # Sem alterações.


class IptuTubaraoSensorStatus(CoordinatorEntity, SensorEntity):
    """Sensor que indica o status de débitos."""
    # Sem alterações.


class IptuTubaraoSensorValorTotalSemJuros(CoordinatorEntity, SensorEntity):
    """Sensor que exibe os valores totais sem juros."""

    def __init__(self, coordinator: IptuTubaraoCoordinator, cpf: str):
        super().__init__(coordinator)
        self._attr_unique_id = f"iptu_tubarao_valor_total_sem_juros_{cpf}"
        self._attr_name = f"Valor Total Sem Juros ({cpf})"
        self._attr_unit_of_measurement = "R$"
        self._attr_icon = "mdi:currency-usd"

    @property
    def native_value(self):
        return self.coordinator.data.get("valores_totais")


class IptuTubaraoSensorValorTotalTaxaUnica(CoordinatorEntity, SensorEntity):
    """Sensor que exibe o valor total da taxa única."""

    def __init__(self, coordinator: IptuTubaraoCoordinator, cpf: str):
        super().__init__(coordinator)
        self._attr_unique_id = f"iptu_tubarao_valor_total_taxa_unica_{cpf}"
        self._attr_name = f"Valor Total Taxa Única ({cpf})"
        self._attr_unit_of_measurement = "R$"
        self._attr_icon = "mdi:currency-usd"

    @property
    def native_value(self):
        return self.coordinator.data.get("valor_total_taxa_unica")


class IptuTubaraoSensorValorTotalSemDesconto(CoordinatorEntity, SensorEntity):
    """Sensor que exibe o valor total sem desconto."""

    def __init__(self, coordinator: IptuTubaraoCoordinator, cpf: str):
        super().__init__(coordinator)
        self._attr_unique_id = f"iptu_tubarao_valor_total_sem_desconto_{cpf}"
        self._attr_name = f"Valor Total Sem Desconto ({cpf})"
        self._attr_unit_of_measurement = "R$"
        self._attr_icon = "mdi:currency-usd"

    @property
    def native_value(self):
        return self.coordinator.data.get("valor_total_sem_desconto")
