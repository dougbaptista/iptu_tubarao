"""Fluxo de configuração para o componente IPTU Tubarão."""
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import TextSelector, TextSelectorConfig

from . import DOMAIN


class IptuTubaraoConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Gerencia o fluxo de configuração para o IPTU Tubarão."""

    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Passo inicial para configuração."""
        errors = {}

        if user_input is not None:
            cpf = user_input["cpf"]

            # Verifica se já existe uma entrada com o mesmo CPF
            if self._cpf_already_configured(cpf):
                errors["base"] = "cpf_exists"
            else:
                # Cria a entrada de configuração
                return self.async_create_entry(
                    title=f"IPTU Tubarão ({cpf})",
                    data={"cpf": cpf},
                )

        schema = vol.Schema(
            {
                vol.Required("cpf"): str,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )

    def _cpf_already_configured(self, cpf: str) -> bool:
        """Verifica se o CPF já está configurado."""
        existing_entries = [entry.data.get("cpf") for entry in self._async_current_entries()]
        return cpf in existing_entries

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Retorna o fluxo de opções."""
        return IptuTubaraoOptionsFlow(config_entry)


class IptuTubaraoOptionsFlow(config_entries.OptionsFlow):
    """Fluxo de opções para o IPTU Tubarão."""

    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Gerencia as opções."""
        errors = {}

        if user_input is not None:
            # Salva as alterações nas opções
            return self.async_create_entry(title="", data=user_input)

        schema = vol.Schema(
            {
                vol.Required("cpf", default=self.config_entry.data["cpf"]): str,
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema, errors=errors)
