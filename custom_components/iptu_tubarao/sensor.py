import logging
import httpx
from bs4 import BeautifulSoup

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = "IPTU Tubarão"


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Configura os sensores a partir de uma config_entry."""
    cpf = entry.data.get("cpf")

    coordinator = IptuTubaraoCoordinator(hass, cpf=cpf)

    # Faz update inicial
    await coordinator.async_config_entry_first_refresh()

    # Criação dos sensores
    entities = [
        IptuTubaraoSensorCPF(coordinator, cpf),
        IptuTubaraoSensorNome(coordinator, cpf),
        IptuTubaraoSensorStatus(coordinator, cpf),
        IptuTubaraoSensorValorTotalSemJuros(coordinator, cpf),
        IptuTubaraoSensorValorTaxaUnica(coordinator, cpf),
        IptuTubaraoSensorValorTotalSemDesconto(coordinator, cpf),
    ]

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

        # Processamento dos valores
        valores = {"valores_totais": 0, "valor_total_unica": 0, "valor_total_sem_desconto": 0}
        tem_debitos = "Não foram localizados débitos" not in soup.get_text()

        if tem_debitos:
            try:
                # VALORES TOTAIS
                valores_totais_element = soup.find("td", string="VALORES TOTAIS:").find_next("td")
                valores["valores_totais"] = float(valores_totais_element.text.replace(".", "").replace(",", "."))

                # VALOR TOTAL ÚNICA
                valor_total_unica_element = soup.find("td", string="VALOR TOTAL ÚNICA:").find_next("td")
                valores["valor_total_unica"] = float(valor_total_unica_element.text.replace(".", "").replace(",", "."))

                # VALOR TOTAL SEM DESCONTO
                valor_total_sem_desconto_element = soup.find("td", string="VALOR SEM DESCONTO:").find_next("td")
                valores["valor_total_sem_desconto"] = float(valor_total_sem_desconto_element.text.replace(".", "").replace(",", "."))
            except Exception as err:
                _LOGGER.error("Erro ao processar valores: %s", err)

        nome_element = soup.select_one("span.mr-2.d-none.d-lg-inline.text-gray-600.small")
        nome_proprietario = nome_element.get_text(strip=True) if nome_element else "Desconhecido"

        return {
            "cpf_formatado": self._formatar_cpf(self._cpf),
            "tem_debitos": tem_debitos,
            "mensagem": "Nenhum débito encontrado" if not tem_debitos else "Débitos localizados",
            "proprietario": nome_proprietario,
            **valores,
        }

    @staticmethod
    def _formatar_cpf(cpf: str) -> str:
        """Formata o CPF com pontuações."""
        cpf = cpf.zfill(11)
        return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"


class IptuTubaraoSensorCPF(CoordinatorEntity, SensorEntity):
    """Sensor que exibe o CPF formatado."""

    def __init__(self, coordinator: IptuTubaraoCoordinator, cpf: str):
        super().__init__(coordinator)
        self._attr_unique_id = f"iptu_tubarao_cpf_{cpf}"
        self._attr_name = f"IPTU Tubarão CPF ({cpf})"
        self._attr_icon = "mdi:account"

    @property
    def native_value(self):
        return self.coordinator.data.get("cpf_formatado")


class IptuTubaraoSensorNome(CoordinatorEntity, SensorEntity):
    """Sensor que exibe o nome do proprietário."""

    def __init__(self, coordinator: IptuTubaraoCoordinator, cpf: str):
        super().__init__(coordinator)
        self._attr_unique_id = f"iptu_tubarao_nome_{cpf}"
        self._attr_name = f"IPTU Tubarão Nome ({cpf})"
        self._attr_icon = "mdi:account-badge"

    @property
    def native_value(self):
        return self.coordinator.data.get("proprietario")


class IptuTubaraoSensorStatus(CoordinatorEntity, SensorEntity):
    """Sensor que indica o status de débitos."""

    def __init__(self, coordinator: IptuTubaraoCoordinator, cpf: str):
        super().__init__(coordinator)
        self._attr_unique_id = f"iptu_tubarao_status_{cpf}"
        self._attr_name = f"IPTU Tubarão Status ({cpf})"
        self._attr_icon = "mdi:alert"

    @property
    def native_value(self):
        return "com_debito" if self.coordinator.data.get("tem_debitos") else "sem_debito"


class IptuTubaraoSensorValorTotalSemJuros(CoordinatorEntity, SensorEntity):
    """Sensor para valores totais sem juros."""

    def __init__(self, coordinator: IptuTubaraoCoordinator, cpf: str):
        super().__init__(coordinator)
        self._attr_unique_id = f"iptu_tubarao_valores_totais_{cpf}"
        self._attr_name = f"Valores Totais Sem Juros ({cpf})"
        self._attr_unit_of_measurement = "R$"
        self._attr_icon = "mdi:currency-usd"

    @property
    def native_value(self):
        return self.coordinator.data.get("valores_totais")


class IptuTubaraoSensorValorTaxaUnica(CoordinatorEntity, SensorEntity):
    """Sensor para o valor total à vista."""

    def __init__(self, coordinator: IptuTubaraoCoordinator, cpf: str):
        super().__init__(coordinator)
        self._attr_unique_id = f"iptu_tubarao_valor_taxa_unica_{cpf}"
        self._attr_name = f"Valor Taxa Única ({cpf})"
        self._attr_unit_of_measurement = "R$"
        self._attr_icon = "mdi:currency-usd"

    @property
    def native_value(self):
        return self.coordinator.data.get("valor_total_unica")


class IptuTubaraoSensorValorTotalSemDesconto(CoordinatorEntity, SensorEntity):
    """Sensor para valor total sem desconto."""

    def __init__(self, coordinator: IptuTubaraoCoordinator, cpf: str):
        super().__init__(coordinator)
        self._attr_unique_id = f"iptu_tubarao_valor_total_sem_desconto_{cpf}"
        self._attr_name = f"Valor Total Sem Desconto ({cpf})"
        self._attr_unit_of_measurement = "R$"
        self._attr_icon = "mdi:currency-usd"

    @property
    def native_value(self):
        return self.coordinator.data.get("valor_total_sem_desconto")
