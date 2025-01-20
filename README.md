# Componente Personalizado: IPTU Tubarão

Este componente customizado para o Home Assistant permite consultar débitos relacionados ao IPTU do município de Tubarão (SC) diretamente na plataforma. Ele exibe informações como o nome do proprietário, status de débitos, valores detalhados e a próxima data de vencimento.

## Funcionalidades

- **CPF Formatado**: Exibe o CPF consultado no formato `XXX.XXX.XXX-XX`.
- **Nome do Proprietário**: Mostra o nome do titular do imóvel registrado.
- **Status de Débitos**: Informa se existem ou não débitos pendentes.
- **Valores Detalhados**:
  - **Valores Totais (Sem Juros)**: Soma total dos débitos.
  - **Valor Taxa Única**: Valor para pagamento à vista.
  - **Valor Total Sem Desconto**: Valor total sem considerar descontos aplicáveis.
- **Próxima Data de Vencimento** (versão 1.4.1): Exibe a data mais próxima de vencimento entre as disponíveis, considerando apenas datas futuras ou iguais a hoje.

## Requisitos

- **Home Assistant**: 2022.7 ou superior.
- **CPF válido**: O CPF precisa estar registrado no sistema de IPTU da Prefeitura de Tubarão.

## Instalação

### Opção 1: Via HACS (Home Assistant Community Store)
1. Certifique-se de que o **HACS** está instalado no seu Home Assistant.
2. No HACS, vá até **Integrações > Repositórios Personalizados** (**Custom Repositories**).
3. Adicione o repositório https://github.com/seu-repositorio/iptu-tubarao do projeto no campo **URL** e selecione o tipo **Integração**:
4. Após adicionar o repositório, vá para a aba **Integrações**, clique em **Explorar e adicionar repositórios** e procure por **IPTU Tubarão**.
5. Instale o componente e reinicie o Home Assistant.
6. Após a reinicialização, vá para **Configurações > Dispositivos e Serviços > Adicionar Integração**, procure por "IPTU Tubarão" e insira o CPF a ser consultado.

### Opção 2: Instalação Manual
1. Copie os arquivos do componente para o diretório `custom_components/iptu_tubarao` na sua instalação do Home Assistant.
2. Reinicie o Home Assistant.
3. No menu de **Configurações**, vá até **Dispositivos e Serviços** e clique em **Adicionar Integração**.
4. Pesquise por "IPTU Tubarão" e insira o CPF a ser consultado.

## Configuração

Após a instalação, adicione a integração via interface do usuário. É necessário fornecer o CPF para configurar o componente.

## Sensores Criados

| Sensor                                      | Descrição                                                                 |
|---------------------------------------------|---------------------------------------------------------------------------|
| `sensor.iptu_tubarao_cpf`                   | Exibe o CPF formatado.                                                   |
| `sensor.iptu_tubarao_nome`                  | Mostra o nome do proprietário.                                           |
| `sensor.iptu_tubarao_status`                | Indica se há débitos (`com_debito` ou `sem_debito`).                     |
| `sensor.iptu_tubarao_valores_totais`        | Exibe o valor total dos débitos (sem juros).                             |
| `sensor.iptu_tubarao_valor_taxa_unica`      | Valor para pagamento único com desconto.                                 |
| `sensor.iptu_tubarao_valor_total_sem_desconto` | Exibe o valor total sem descontos aplicáveis.                            |
| `sensor.iptu_tubarao_proxima_data_vencimento` | Exibe a data mais próxima de vencimento (adicionado na versão 1.4.1).   |

## Atualizações

### Versão 1.4.1
- Adicionado o sensor `proxima_data_vencimento`, que exibe a data mais próxima de vencimento, considerando apenas datas futuras ou iguais a hoje.
- Atualização das informações configurada para ser feita automaticamente uma vez por dia.

### Versão 1.4.0
- Correções de bugs na captura de valores financeiros.
- Melhorias na formatação do CPF.

### Versão 1.3.0
- Adicionado suporte ao sensor de valor total sem desconto.
- Melhorias na captura do nome do proprietário.

## Logs

Os logs podem ser visualizados no Home Assistant para monitorar erros ou verificar o comportamento do componente.

Para habilitar logs detalhados, adicione o seguinte ao arquivo `configuration.yaml`:

```yaml
logger:
default: warning
logs:
 custom_components.iptu_tubarao: debug
