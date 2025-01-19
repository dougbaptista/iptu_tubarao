"""Config Flow para integração do IPTU Tubarão."""
import voluptuous as vol
from homeassistant import config_entries
import httpx

from . import DOMAIN

class IptuTubaraoConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Fluxo de configuração para IPTU Tubarão."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Primeiro passo do fluxo de configuração."""
        errors = {}

        if user_input is not None:
            cpf = user_input["cpf"].replace(".", "").replace("-", "")
            
            # Valida o CPF antes de criar a entrada
            if not await self._validate_cpf(cpf):
                errors["cpf"] = "invalid_cpf"
            else:
                # CPF válido, cria a entrada
                return self.async_create_entry(
                    title=f"IPTU Tubarão ({cpf})",
                    data={"cpf": cpf},
                )

        data_schema = vol.Schema({
            vol.Required("cpf"): str,
        })

        return self.async_show_form(step_id="user", data_schema=data_schema, errors=errors)

    async def _validate_cpf(self, cpf):
        """
        Verifica se o CPF é válido ao consultar a API.
        Retorna True se válido, False caso contrário.
        """
        url = "https://tubarao-sc.prefeituramoderna.com.br/meuiptu/index.php?cidade=tubarao"
        form_data = {
            "documento": cpf,
            "inscricao": "",
            "st_menu": "1",
        }

        async with httpx.AsyncClient() as client:
            try:
                # Tenta acessar o serviço com o CPF fornecido
                response = await client.post(url, data=form_data, timeout=30)
                response.raise_for_status()
                
                # Verifica se a resposta indica erro de acesso
                if "As informações de acesso estão inválidas." in response.text:
                    return False
            except Exception:
                # Em caso de erro de conexão, assume CPF inválido
                return False
        
        return True
