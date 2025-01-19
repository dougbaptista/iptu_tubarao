# IPTU Tubarão - Componente Customizado para Home Assistant

Este repositório contém um **componente customizado** para o Home Assistant que consulta o site de IPTU da Prefeitura de Tubarão/SC, informando se existe algum débito para determinado CPF.

> **Atenção**  
> Este projeto é **apenas um protótipo** e pode precisar de ajustes para lidar com mudanças no site oficial, variações de layout, captchas, sessões, cookies ou outros mecanismos de segurança.  
> Ele também não garante suporte contínuo caso a prefeitura altere o sistema.

---

## Instalação via HACS

1. No Home Assistant, abra **HACS** e vá em **Integrations**.
2. No canto superior direito, clique no menu de três pontos e depois em **Custom repositories**.
3. Adicione o repositório deste projeto (URL do seu GitHub) selecionando “Integration” em **Category**.
4. Depois de adicionar, a integração aparecerá para ser instalada como qualquer outra no HACS.
5. Reinicie o Home Assistant após a instalação.

---

## Configuração

1. No Home Assistant, vá em **Configurações** > **Dispositivos e Serviços**.
2. Clique em **Adicionar Integração** e procure por “IPTU Tubarão”.
3. Informe seu **CPF** (utilizado pelo site de IPTU).
4. Opcionalmente, defina um **nome** para este sensor.
5. Conclua o fluxo de configuração.

Após isso, será criado um sensor com estado:
- `com_debito` se houver débito.
- `sem_debito` se não houver débito.

O sensor também traz um atributo `mensagem` com detalhes adicionais fornecidos pelo site.

---

## Funcionamento Interno (Resumo)

- O componente faz um **POST** do CPF no site da Prefeitura, simulando o preenchimento de formulário.
- Em seguida, analisa a resposta e busca pelo texto que indica “Não foram localizados débitos” ou similar.
- Se encontrar, assume que não há débitos (`sem_debito`).
- Caso contrário, assume que há débito (`com_debito`).

---

## Limitações

- **Captchas e Sessões**: Se o site exigir captcha, sessão autenticada ou outro mecanismo, o componente pode falhar.
- **Frequência de Atualização**: Por padrão, faz um check inicial. Você pode ajustar o `update_interval` no código para consultar diariamente ou na frequência desejada (ajustando o `DataUpdateCoordinator`).
- **Mudanças no Site**: Qualquer alteração no layout do site pode quebrar o parse do HTML. Caso isso ocorra, será necessário ajustar o código.

---

## Roadmap de Melhorias

- [ ] Tornar a coleta de dados mais robusta e tratar eventuais captchas.  
- [ ] Adicionar suporte a _múltiplos imóveis_ (por exemplo, se a pessoa tiver mais de um).  
- [ ] Permitir configuração da **frequência** de checagem na interface.  
- [ ] Lidar com exceções de conexão de forma mais detalhada.

---

## Contribuindo

Contribuições são bem-vindas!

1. Faça um _fork_ do repositório.
2. Crie sua _branch_ com o patch/feature (`git checkout -b minha-feature`).
3. Faça o _commit_ e _push_ (`git push origin minha-feature`).
4. Abra um _pull request_ descrevendo suas alterações.

---

**Observação**: Este projeto é independente e não possui vínculo oficial com a Prefeitura de Tubarão. Use por sua conta e risco.
