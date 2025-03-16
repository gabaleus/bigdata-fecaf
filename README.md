# Painel de Análise de Temperaturas (Temperature Log Dashboard)

Uma aplicação Streamlit para upload, armazenamento e visualização de dados de logs de temperatura com integração PostgreSQL.

## Funcionalidades

- **Upload de Dados**: Importação de arquivos CSV contendo registros de temperatura.
- **Processamento de Dados**: Limpeza e formatação automática dos dados importados.
- **Armazenamento em Banco de Dados**: Persistência dos dados em banco PostgreSQL.
- **Visualizações Interativas**: 
  - Gráficos de linha mostrando variações de temperatura ao longo do tempo
  - Histogramas com distribuição das temperaturas
  - Filtros por localização (interna/externa) e período
- **Estatísticas**: Análise estatística detalhada dos dados de temperatura

## Tecnologias Utilizadas

- **Streamlit**: Framework para criação da interface do usuário
- **Pandas**: Processamento e manipulação de dados
- **SQLAlchemy**: ORM para interação com o banco de dados
- **PostgreSQL**: Banco de dados relacional
- **Plotly**: Criação de visualizações interativas

## Como Executar

1. Clone o repositório:
```
git clone https://github.com/seu-usuario/temperature-dashboard.git
cd temperature-dashboard
```

2. Instale as dependências:
```
pip install -r requirements.txt
```

3. Configure as variáveis de ambiente:
Crie um arquivo `.env` com as configurações de conexão ao banco de dados PostgreSQL:
```
DATABASE_URL=postgresql://usuario:senha@localhost:5432/nome_do_banco
```

4. Execute a aplicação:
```
streamlit run main.py
```

## Estrutura do Projeto

- `main.py`: Arquivo principal da aplicação Streamlit
- `.streamlit/config.toml`: Configurações do Streamlit
- `requirements.txt`: Dependências do projeto

## Formato dos Dados

O aplicativo espera arquivos CSV com as seguintes colunas:
- `id`: Identificador único do registro
- `room_id/id`: Identificador da sala/local
- `noted_date`: Data e hora da medição (formato DD-MM-YYYY HH:MM)
- `temp`: Temperatura registrada
- `out/in`: Indicador se a medição é interna ("In") ou externa ("Out")