# Componente Personalizado: IPTU Tubarão

Este componente customizado para o [Home Assistant](https://www.home-assistant.io/) permite consultar débitos relacionados ao IPTU do município de Tubarão (SC) diretamente na plataforma. Ele exibe informações como o nome do proprietário, status de débitos e valores detalhados.

## Funcionalidades

- **CPF Formatado**: Exibe o CPF consultado no formato `XXX.XXX.XXX-XX`.
- **Nome do Proprietário**: Mostra o nome do titular do imóvel registrado.
- **Status de Débitos**: Informa se existem ou não débitos pendentes.
- **Valores Detalhados**:
  - **Valores Totais (Sem Juros)**: Soma total dos débitos.
  - **Valor Taxa Única**: Valor para pagamento à vista.
  - **Valor Total Sem Desconto**: Valor total sem considerar descontos aplicáveis.

## Requisitos

- Home Assistant 2022.7 ou superior.
- CPF válido e registrado no sistema de IPTU da Prefeitura de Tubarão.

## Instalação

1. Copie os arquivos do componente para o diretório `custom_components/iptu_tubarao` na sua instalação do Home Assistant.
2. Reinicie o Home Assistant.
3. No menu de **Configurações**, vá até **Dispositivos e Serviços** e clique em **Adicionar Integração**.
4. Pesquise por "IPTU Tubarão" e insira o CPF a ser consultado.

## Configuração

Após a instalação, você pode adicionar a integração via interface do usuário. É necessário fornecer o CPF para configurar o componente.

## Sensores Criados

- `sensor.iptu_tubarao_cpf`: Exibe o CPF formatado.
- `sensor.iptu_tubarao_nome`: Mostra o nome do proprietário.
- `sensor.iptu_tubarao_status`: Indica se há débitos (`com_debito` ou `sem_debito`).
- `sensor.iptu_tubarao_valores_totais`: Exibe o valor total dos débitos (sem juros).
- `sensor.iptu_tubarao_valor_taxa_unica`: Valor para pagamento único com desconto.
- `sensor.iptu_tubarao_valor_total_sem_desconto`: Exibe o valor total sem descontos aplicáveis.

## Logs

Os logs podem ser visualizados no Home Assistant para monitorar erros ou verificar o comportamento do componente.

Para habilitar logs detalhados, adicione o seguinte ao arquivo `configuration.yaml`:

```yaml
logger:
  default: warning
  logs:
    custom_components.iptu_tubarao: debug
