"""Config Flow para integração do IPTU Tubarão."""
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_NAME

from . import DOMAIN


class IptuTubaraoConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Fluxo de configuração para IPTU Tubarão."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Primeiro passo do fluxo de configuração."""
        errors = {}

        if user_input is not None:
            cpf = user_input["cpf"].replace(".", "").replace("-", "")
            return self.async_create_entry(
                title="IPTU Tubarão",
                data={"cpf": cpf, "name": user_input[CONF_NAME]},
            )

        data_schema = vol.Schema({
            vol.Required("cpf"): str,
            vol.Optional(CONF_NAME, default="IPTU Tubarão"): str,
        })

        return self.async_show_form(step_id="user", data_schema=data_schema, errors=errors)
