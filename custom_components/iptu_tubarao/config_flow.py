from homeassistant import config_entries
from homeassistant.core import callback

DOMAIN = "iptu_tubarao"

class IptuTubaraoConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for IPTU Tubarão."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        if user_input is not None:
            # Validação do input do usuário
            return self.async_create_entry(title="IPTU Tubarão", data=user_input)

        # Exibir formulário inicial
        return self.async_show_form(step_id="user")
