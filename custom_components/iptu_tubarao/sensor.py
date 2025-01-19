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
    """Configura os sensores a partir de uma config_entry."""
    cpf = entry.data.get("cpf")

    coordinator = IptuTubaraoCoordinator(hass, cpf=cpf)
    # Faz update inicial
    await coordinator.async_config_entry_first_refresh()

    entities = [
        IptuTubaraoSensorCPF(coordinator, cpf),
        IptuTubaraoSensorNome(coordinator, cpf),
        IptuTubaraoSensorStatus(coordinator, cpf)
    ]

    # Adicionar sensores de valores somente se houver débitos
    if coordinator.data.get("tem_debitos"):
        entities.extend([
            IptuTubaraoSensorValoresTotais(coordinator, cpf),
            IptuTubaraoSensorValorTotalUnica(coordinator, cpf)
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
        """
        Faz POST do CPF e coleta se há débitos e o nome do proprietário.
        """
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
        tem_debitos = "Não foram localizados débitos" not in soup.get_text()

        valores_totais = None
        valor_total_unica = None

        if tem_debitos:
            # Extrair valores de débitos
            try:
                valores_totais_element = soup.select_one("td.text-nowrap div[align='right']")
                valores_totais = float(valores_totais_element.text.replace(".", "").replace(",", ".")) if valores_totais_element else 0

                valor_total_unica_element = soup.select("td.d-print-table-cell b div[align='right']")[-1]
                valor_total_unica = float(valor_total_unica_element.text.replace(".", "").replace(",", ".")) if valor_total_unica_element else 0
            except Exception as err:
                _LOGGER.error("Erro ao processar valores de débitos: %s", err)

        # Busca o nome no local correto
        nome_element = soup.select_one("span.mr-2.d-none.d-lg-inline.text-gray-600.small")
        nome_proprietario = nome_element.get_text(strip=True) if nome_element else "Desconhecido"

        return {
            "cpf_formatado": self._formatar_cpf(self._cpf),
            "tem_debitos": tem_debitos,
            "mensagem": "Nenhum débito encontrado" if not tem_debitos else "Foi localizado algum débito!",
            "proprietario": nome_proprietario,
            "valores_totais": valores_totais,
            "valor_total_unica": valor_total_unica,
        }

    @staticmethod
    def _formatar_cpf(cpf: str) -> str:
        """Formata o CPF com pontuações."""
        cpf = cpf.zfill(11)  # Adiciona zeros à esquerda, se necessário
        return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"


class IptuTubaraoSensorCPF(CoordinatorEntity, SensorEntity):
    """Sensor que exibe o CPF formatado."""

    def __init__(self, coordinator: IptuTubaraoCoordinator, cpf: str):
        """Inicializa o sensor."""
        super().__init__(coordinator)
        self._cpf = cpf
        self._attr_unique_id = f"iptu_tubarao_cpf_{cpf}"
        self._attr_name = f"IPTU Tubarão CPF ({cpf})"
        self._attr_icon = "mdi:account"

    @property
    def native_value(self):
        """Retorna o CPF formatado."""
        return self.coordinator.data.get("cpf_formatado")


class IptuTubaraoSensorNome(CoordinatorEntity, SensorEntity):
    """Sensor que exibe o nome do proprietário."""

    def __init__(self, coordinator: IptuTubaraoCoordinator, cpf: str):
        """Inicializa o sensor."""
        super().__init__(coordinator)
        self._cpf = cpf
        self._attr_unique_id = f"iptu_tubarao_nome_{cpf}"
        self._attr_name = f"IPTU Tubarão Nome ({cpf})"
        self._attr_icon = "mdi:account-badge"

    @property
    def native_value(self):
        """Retorna o nome do proprietário."""
        return self.coordinator.data.get("proprietario")


class IptuTubaraoSensorStatus(CoordinatorEntity, SensorEntity):
    """Sensor que indica o status de débitos."""

    def __init__(self, coordinator: IptuTubaraoCoordinator, cpf: str):
        """Inicializa o sensor."""
        super().__init__(coordinator)
        self._cpf = cpf
        self._attr_unique_id = f"iptu_tubarao_status_{cpf}"
        self._attr_name = f"IPTU Tubarão Status ({cpf})"
        self._attr_icon = "mdi:alert"

    @property
    def native_value(self):
        """Retorna o status de débitos."""
        return "com_debito" if self.coordinator.data.get("tem_debitos") else "sem_debito"

    @property
    def extra_state_attributes(self):
        """Retorna detalhes extras, como a mensagem."""
        return {
            "mensagem": self.coordinator.data.get("mensagem", "")
        }

    @property
    def device_info(self) -> DeviceInfo:
        """Agrupa como dispositivo no Home Assistant."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._cpf)},
            name=f"IPTU Tubarão ({self._cpf})",
            manufacturer="Prefeitura de Tubarão",
            model="Consulta IPTU Online",
        )


class IptuTubaraoSensorValoresTotais(CoordinatorEntity, SensorEntity):
    """Sensor que exibe os valores totais de débitos."""

    def __init__(self, coordinator: IptuTubaraoCoordinator, cpf: str):
        """Inicializa o sensor."""
        super().__init__(coordinator)
        self._cpf = cpf
        self._attr_unique_id = f"iptu_tubarao_valores_totais_{cpf}"
        self._attr_name = f"Valores Totais ({cpf})"
        self._attr_unit_of_measurement = "R$"
        self._attr_icon = "mdi:currency-usd"

    @property
    def native_value(self):
        """Retorna os valores totais."""
        return self.coordinator.data.get("valores_totais")


class IptuTubaraoSensorValorTotalUnica(CoordinatorEntity, SensorEntity):
    """Sensor que exibe o valor total à vista."""

    def __init__(self, coordinator: IptuTubaraoCoordinator, cpf: str):
        """Inicializa o sensor."""
        super().__init__(coordinator)
        self._cpf = cpf
        self._attr_unique_id = f"iptu_tubarao_valor_total_unica_{cpf}"
        self._attr_name = f"Valor Total Única ({cpf})"
        self._attr_unit_of_measurement = "R$"
        self._attr_icon = "mdi:currency-usd"

    @property
    def native_value(self):
        """Retorna o valor total à vista."""
        return self.coordinator.data.get("valor_total_unica")
