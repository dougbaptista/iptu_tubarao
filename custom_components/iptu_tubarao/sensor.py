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
    cpf = entry.data.get("cpf")

    coordinator = IptuTubaraoCoordinator(hass, cpf=cpf)

    await coordinator.async_config_entry_first_refresh()

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
    def __init__(self, hass: HomeAssistant, cpf: str):
        super().__init__(
            hass,
            _LOGGER,
            name=f"iptu_tubarao_coordinator_{cpf}",
        )
        self._cpf = cpf
        self._session = httpx.AsyncClient(verify=True)

    async def _async_update_data(self):
        return await self._fetch_debitos()

    async def _fetch_debitos(self):
        url = "https://tubarao-sc.prefeituramoderna.com.br/meuiptu/index.php?cidade=tubarao"

        try:
            response = await self._session.get(url, timeout=30)
            response.raise_for_status()
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

        _LOGGER.debug("HTML recebido: %s", soup.prettify())

        valores = {
            "valores_totais": 0,
            "valor_total_unica": 0,
            "valor_total_sem_desconto": 0,
        }
        tem_debitos = "Não foram localizados débitos" not in soup.get_text()

        if tem_debitos:
            try:
                # Busca por "VALORES TOTAIS"
                valores_totais_element = soup.find("td", string=lambda text: text and "VALORES TOTAIS" in text.upper())
                if valores_totais_element:
                    valores["valores_totais"] = float(
                        valores_totais_element.find_next("td").text.strip().replace(".", "").replace(",", ".")
                    )
                    _LOGGER.debug("VALORES TOTAIS: %s", valores["valores_totais"])

                # Busca por "VALOR TOTAL ÚNICA"
                valor_total_unica_element = soup.find("td", string=lambda text: text and "VALOR TOTAL ÚNICA" in text.upper())
                if valor_total_unica_element:
                    valores["valor_total_unica"] = float(
                        valor_total_unica_element.find_next("td").text.strip().replace(".", "").replace(",", ".")
                    )
                    _LOGGER.debug("VALOR TOTAL ÚNICA: %s", valores["valor_total_unica"])

                # Busca por "VALOR SEM DESCONTO"
                valor_total_sem_desconto_element = soup.find("td", string=lambda text: text and "VALOR SEM DESCONTO" in text.upper())
                if valor_total_sem_desconto_element:
                    valores["valor_total_sem_desconto"] = float(
                        valor_total_sem_desconto_element.find_next("td").text.strip().replace(".", "").replace(",", ".")
                    )
                    _LOGGER.debug("VALOR SEM DESCONTO: %s", valores["valor_total_sem_desconto"])
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
        cpf = cpf.zfill(11)
        return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"


class IptuTubaraoSensorCPF(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator: IptuTubaraoCoordinator, cpf: str):
        super().__init__(coordinator)
        self._attr_unique_id = f"iptu_tubarao_cpf_{cpf}"
        self._attr_name = f"IPTU Tubarão CPF ({cpf})"
        self._attr_icon = "mdi:account"

    @property
    def native_value(self):
        return self.coordinator.data.get("cpf_formatado")


class IptuTubaraoSensorNome(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator: IptuTubaraoCoordinator, cpf: str):
        super().__init__(coordinator)
        self._attr_unique_id = f"iptu_tubarao_nome_{cpf}"
        self._attr_name = f"IPTU Tubarão Nome ({cpf})"
        self._attr_icon = "mdi:account-badge"

    @property
    def native_value(self):
        return self.coordinator.data.get("proprietario")


class IptuTubaraoSensorValorTotalSemJuros(CoordinatorEntity, SensorEntity):
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
    def __init__(self, coordinator: IptuTubaraoCoordinator, cpf: str):
        super().__init__(coordinator)
        self._attr_unique_id = f"iptu_tubarao_valor_total_sem_desconto_{cpf}"
        self._attr_name = f"Valor Total Sem Desconto ({cpf})"
        self._attr_unit_of_measurement = "R$"
        self._attr_icon = "mdi:currency-usd"

    @property
    def native_value(self):
        return self.coordinator.data.get("valor_total_sem_desconto")
