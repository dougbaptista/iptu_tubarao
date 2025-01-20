import logging
import httpx
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = "IPTU Tubarão"

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Configura os sensores a partir de uma config_entry."""
    cpf = entry.data.get("cpf")

    # Cria o coordenador com atualização diária
    coordinator = IptuTubaraoCoordinator(hass, cpf=cpf)
    await coordinator.async_config_entry_first_refresh()

    # Define os sensores
    entities = [
        IptuTubaraoSensorCPF(coordinator, cpf),
        IptuTubaraoSensorNome(coordinator, cpf),
        IptuTubaraoSensorStatus(coordinator, cpf),
        IptuTubaraoSensorValorTotalSemJuros(coordinator, cpf),
        IptuTubaraoSensorValorTaxaUnica(coordinator, cpf),
        IptuTubaraoSensorValorTotalSemDesconto(coordinator, cpf),
        IptuTubaraoSensorProximaDataVencimento(coordinator, cpf),
    ]

    async_add_entities(entities, update_before_add=True)

class IptuTubaraoCoordinator(DataUpdateCoordinator):
    """Coordenador para buscar os dados periodicamente."""

    def __init__(self, hass: HomeAssistant, cpf: str):
        super().__init__(
            hass,
            _LOGGER,
            name=f"iptu_tubarao_coordinator_{cpf}",
            update_interval=timedelta(days=1),  # Atualiza uma vez por dia
        )
        self._cpf = cpf
        self._session = httpx.AsyncClient(verify=True)

    async def _async_update_data(self):
        """Busca os dados no site e retorna como dicionário."""
        return await self._fetch_debitos()

    async def _fetch_debitos(self):
        """Faz a requisição ao site e processa os dados."""
        url = "https://tubarao-sc.prefeituramoderna.com.br/meuiptu/index.php?cidade=tubarao"

        try:
            # Acessa a página inicial
            await self._session.get(url, timeout=30)
        except Exception as err:
            _LOGGER.error("Erro ao acessar URL inicial: %s", err)
            raise

        form_data = {"documento": self._cpf, "inscricao": "", "st_menu": "1"}

        try:
            # Envia o CPF no formulário
            response = await self._session.post(url, data=form_data, timeout=30)
            response.raise_for_status()
        except Exception as err:
            _LOGGER.error("Erro ao enviar CPF: %s", err)
            raise

        soup = BeautifulSoup(response.text, "html.parser")
        _LOGGER.debug("HTML recebido: %s", soup.prettify())

        # Inicializa os dados
        data = {
            "cpf_formatado": self._formatar_cpf(self._cpf),
            "tem_debitos": False,
            "mensagem": "Nenhum débito encontrado",
            "proprietario": "Desconhecido",
            "valores_totais": 0.0,
            "valor_total_unica": 0.0,
            "valor_total_sem_desconto": 0.0,
            "proxima_data_vencimento": None,
        }

        # Verifica se há débitos
        if "Não foram localizados débitos" not in soup.get_text():
            data["tem_debitos"] = True
            data["mensagem"] = "Débitos localizados"

            try:
                # Captura VALORES TOTAIS
                valores_totais_element = soup.find("td", string="VALORES TOTAIS:")
                if valores_totais_element:
                    valor_texto = valores_totais_element.find_next("td").text.strip()
                    data["valores_totais"] = float(valor_texto.replace(".", "").replace(",", "."))

                # Captura VALOR TAXA ÚNICA
                valor_taxa_unica_element = soup.find("td", string="VALOR TOTAL ÚNICA:")
                if valor_taxa_unica_element:
                    valor_texto = valor_taxa_unica_element.find_next("td").text.strip()
                    data["valor_total_unica"] = float(valor_texto.replace(".", "").replace(",", "."))

                # Captura VALOR SEM DESCONTO
                td_elements = soup.find_all('td', class_='pt-2')
                if td_elements:
                    td = td_elements[-1]
                    div = td.find('div', style="border-top:#999999 1px solid;")
                    if div:
                        valor_texto = div.get_text(strip=True)
                        data["valor_total_sem_desconto"] = float(valor_texto.replace(".", "").replace(",", "."))

                # Captura todas as datas de vencimento
                datas = []
                for td in td_elements:
                    date_div = td.find("div", align="center")
                    if date_div:
                        date_str = date_div.get_text(strip=True)
                        try:
                            date_obj = datetime.strptime(date_str, "%d/%m/%Y")
                            datas.append(date_obj)
                        except ValueError:
                            continue

                # Filtra datas futuras ou iguais a hoje e encontra a menor
                hoje = datetime.today()
                futuras = [d for d in datas if d >= hoje]
                if futuras:
                    proxima_data = min(futuras)
                    data["proxima_data_vencimento"] = proxima_data.strftime("%d/%m/%Y")

            except Exception as err:
                _LOGGER.error("Erro ao processar valores: %s", err)

        # Captura o nome do proprietário
        nome_element = soup.select_one("span.mr-2.d-none.d-lg-inline.text-gray-600.small")
        if nome_element:
            data["proprietario"] = nome_element.get_text(strip=True)

        return data

    @staticmethod
    def _formatar_cpf(cpf: str) -> str:
        """Formata o CPF no padrão XXX.XXX.XXX-XX."""
        cpf = cpf.zfill(11)
        return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"


# Sensores
class IptuTubaraoSensorCPF(CoordinatorEntity, SensorEntity):
    """Sensor para exibir o CPF formatado."""
    def __init__(self, coordinator, cpf):
        super().__init__(coordinator)
        self._attr_unique_id = f"iptu_tubarao_cpf_{cpf}"
        self._attr_name = "CPF Formatado"
        self._attr_icon = "mdi:account"

    @property
    def native_value(self):
        return self.coordinator.data.get("cpf_formatado")


class IptuTubaraoSensorNome(CoordinatorEntity, SensorEntity):
    """Sensor para exibir o nome do proprietário."""
    def __init__(self, coordinator, cpf):
        super().__init__(coordinator)
        self._attr_unique_id = f"iptu_tubarao_nome_{cpf}"
        self._attr_name = "Nome do Proprietário"
        self._attr_icon = "mdi:account-badge"

    @property
    def native_value(self):
        return self.coordinator.data.get("proprietario")


class IptuTubaraoSensorStatus(CoordinatorEntity, SensorEntity):
    """Sensor para exibir o status de débitos."""
    def __init__(self, coordinator, cpf):
        super().__init__(coordinator)
        self._attr_unique_id = f"iptu_tubarao_status_{cpf}"
        self._attr_name = "Status de Débitos"
        self._attr_icon = "mdi:alert"

    @property
    def native_value(self):
        return "com_debito" if self.coordinator.data.get("tem_debitos") else "sem_debito"


class IptuTubaraoSensorValorTotalSemJuros(CoordinatorEntity, SensorEntity):
    """Sensor para VALORES TOTAIS."""
    def __init__(self, coordinator, cpf):
        super().__init__(coordinator)
        self._attr_unique_id = f"iptu_tubarao_valores_totais_{cpf}"
        self._attr_name = "Valores Totais (Sem Juros)"
        self._attr_unit_of_measurement = "R$"
        self._attr_icon = "mdi:currency-usd"

    @property
    def native_value(self):
        return self.coordinator.data.get("valores_totais")


class IptuTubaraoSensorValorTaxaUnica(CoordinatorEntity, SensorEntity):
    """Sensor para VALOR TAXA ÚNICA."""
    def __init__(self, coordinator, cpf):
        super().__init__(coordinator)
        self._attr_unique_id = f"iptu_tubarao_valor_taxa_unica_{cpf}"
        self._attr_name = "Valor Taxa Única"
        self._attr_unit_of_measurement = "R$"
        self._attr_icon = "mdi:currency-usd"

    @property
    def native_value(self):
        return self.coordinator.data.get("valor_total_unica")


class IptuTubaraoSensorValorTotalSemDesconto(CoordinatorEntity, SensorEntity):
    """Sensor para VALOR SEM DESCONTO."""
    def __init__(self, coordinator, cpf):
        super().__init__(coordinator)
        self._attr_unique_id = f"iptu_tubarao_valor_total_sem_desconto_{cpf}"
        self._attr_name = "Valor Total Sem Desconto"
        self._attr_unit_of_measurement = "R$"
        self._attr_icon = "mdi:currency-usd"

    @property
    def native_value(self):
        return self.coordinator.data.get("valor_total_sem_desconto")


class IptuTubaraoSensorProximaDataVencimento(CoordinatorEntity, SensorEntity):
    """Sensor para a próxima data de vencimento."""
    def __init__(self, coordinator, cpf):
        super().__init__(coordinator)
        self._attr_unique_id = f"iptu_tubarao_proxima_data_vencimento_{cpf}"
        self._attr_name = "Próxima Data de Vencimento"
        self._attr_icon = "mdi:calendar"

    @property
    def native_value(self):
        return self.coordinator.data.get("proxima_data_vencimento")
