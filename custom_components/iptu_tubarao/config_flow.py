from homeassistant import config_entries
from homeassistant.core import callback

class IptuTubaraoConfigFlow(config_entries.ConfigFlow, domain="iptu_tubarao"):
    """Handle a config flow for IPTU Tubarão."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        if user_input is not None:
            # Valide a entrada do usuário e prossiga
            return self.async_create_entry(title="IPTU Tubarão", data=user_input)

        # Retorne um formulário para o usuário preencher
        return self.async_show_form(step_id="user")
