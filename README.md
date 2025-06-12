# 📊 Dashboard de Análise de Carteira - Warren

Um dashboard interativo desenvolvido em Streamlit para análise de carteira de investimentos com persistência de dados via Google Sheets.

## 🚀 Funcionalidades

- **📁 Upload de Planilha**: Faça upload de uma planilha Excel/CSV com seus ativos e quantidades
- **💾 Persistência de Dados**: Salve seus portfólios automaticamente no Google Sheets
- **📚 Gerenciamento de Portfólios**: Gerencie múltiplos portfólios (IDIV, IFIX, etc.) com histórico de versões
- **💰 Análise de Dividendos**: Visualize dividendos e análise de volume com dados em tempo real
- **📈 Resumo da Carteira**: Análise completa da distribuição da carteira por ativo
- **🎯 Gráficos Interativos**: Visualizações profissionais com Plotly
- **🔍 Comparação de Versões**: Compare diferentes versões dos seus portfólios
- **☁️ Deploy na Nuvem**: Pronto para Streamlit Cloud

## 📋 Pré-requisitos

- Python 3.7 ou superior
- Conexão com internet (para buscar dados do Yahoo Finance)

## 🛠️ Instalação

1. Clone ou baixe este repositório
2. Instale as dependências:

```bash
pip install -r requirements.txt
```

## ▶️ Como Executar

Execute o comando no terminal:

```bash
streamlit run dashboard_dividendos.py
```

O dashboard será aberto automaticamente no seu navegador em `http://localhost:8501`

## 📊 Como Usar

### 1. Upload da Planilha
- Prepare um arquivo com as colunas:
  - **Ativo**: Código do ativo (ex: PETR4, VALE3, ITUB4)
  - **Quantidade**: Quantidade de ações
- Formatos aceitos:
  - **Excel**: .xlsx, .xls
  - **CSV**: .csv (separadores detectados automaticamente: ; , tab)
- Faça upload na primeira aba

### 2. Análise de Dividendos
- Selecione o período de análise (1 ano, 6 meses ou 3 meses)
- Visualize:
  - Valor total da carteira
  - Dividend yield médio
  - Total de dividendos recebidos
  - Distribuição por ativo
  - Gráficos interativos

### 3. Resumo da Carteira
- Visualize análise por setor
- Top 5 maiores posições
- Top 5 maiores dividend yields
- Distribuição treemap por setor

## 📁 Exemplos de Arquivos

### Excel (.xlsx)
| Ativo | Quantidade |
|-------|------------|
| PETR4 | 100        |
| VALE3 | 50         |
| ITUB4 | 200        |
| BBDC4 | 150        |
| ABEV3 | 300        |

### CSV (separador ;)
```csv
Ativo;Quantidade
PETR4;100
VALE3;50
ITUB4;200
```

### CSV (separador ,)
```csv
Ativo,Quantidade
PETR4,100
VALE3,50
ITUB4,200
```

## 🔧 Dependências

- `streamlit`: Interface web interativa
- `pandas`: Manipulação de dados
- `yfinance`: Dados financeiros em tempo real
- `plotly`: Gráficos interativos
- `openpyxl`: Leitura de arquivos Excel
- `numpy`: Computação numérica
- `gspread`: Integração com Google Sheets
- `google-auth`: Autenticação Google

## 📈 Dados Suportados

- Ações brasileiras da B3 (automaticamente adiciona .SA)
- Ações internacionais (especificar extensão completa)
- Dados em tempo real via Yahoo Finance
- Histórico de dividendos

## 🎯 Funcionalidades Técnicas

- **Leitura robusta**: Detecta automaticamente encoding e separadores de CSV
- **Cache de dados**: Performance otimizada com cache do Streamlit
- **Tratamento de erros**: Gestão robusta de erros de API e arquivo
- **Responsivo**: Interface adaptável a diferentes tamanhos de tela
- **Tempo real**: Dados atualizados automaticamente
- **Múltiplos formatos**: Suporte para Excel (.xlsx, .xls) e CSV

## 🆘 Solução de Problemas

### Erro ao buscar dados de um ativo
- Verifique se o código do ativo está correto
- Para ações brasileiras, use apenas o código (ex: PETR4)
- Para ações internacionais, inclua a extensão (ex: AAPL)

### Planilha não carrega
- Verifique se as colunas estão nomeadas exatamente como "Ativo" e "Quantidade"
- Certifique-se de que o arquivo é .xlsx ou .xls
- Verifique se não há células vazias nas colunas principais

### Performance lenta
- Reduza o número de ativos na planilha para testes
- Use o botão "Atualizar Dados" para limpar o cache se necessário

## 📞 Suporte

Em caso de dúvidas ou problemas, verifique:
1. Se todas as dependências estão instaladas
2. Se a conexão com internet está funcionando
3. Se os códigos dos ativos estão corretos

---

## ☁️ **Deploy no Streamlit Cloud**

### **1. 🔐 Configurar Google Sheets API**

1. Acesse [Google Cloud Console](https://console.cloud.google.com/)
2. Crie um novo projeto ou selecione um existente
3. Ative a **Google Sheets API** e **Google Drive API**
4. Crie credenciais de **Service Account**
5. Baixe o arquivo JSON das credenciais
6. Compartilhe suas planilhas com o email do service account

### **2. 🚀 Deploy no Streamlit Cloud**

1. Acesse [share.streamlit.io](https://share.streamlit.io)
2. Conecte com seu GitHub
3. Escolha este repositório
4. Configure os **Secrets** no painel:

```toml
[gcp_service_account]
type = "service_account"
project_id = "seu-project-id"
private_key_id = "sua-private-key-id"
private_key = "-----BEGIN PRIVATE KEY-----\nSUA_CHAVE_PRIVADA\n-----END PRIVATE KEY-----\n"
client_email = "seu-service-account@projeto.iam.gserviceaccount.com"
client_id = "seu-client-id"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/..."

admin_email = "seu-email@gmail.com"
```

5. Clique em **Deploy**! 🎉

### **3. 📁 Estrutura dos Arquivos**

```bash
📦 dashboard/
├── 📄 dashboard_dividendos.py    # App principal
├── 📄 portfolio_manager.py       # Gerenciador Google Sheets
├── 📄 requirements.txt           # Dependências
├── 📄 .gitignore                # Arquivos ignorados
├── 📂 .streamlit/
│   └── 📄 secrets.toml          # Credenciais (local)
└── 📄 README.md                 # Este arquivo
```

### **4. 🔧 Configuração Local (Opcional)**

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/dashboard.git
cd dashboard

# Instale dependências
pip install -r requirements.txt

# Configure secrets localmente
# Edite .streamlit/secrets.toml com suas credenciais

# Execute localmente
streamlit run dashboard_dividendos.py
```

---

## 🆘 **Solução de Problemas**

### **Google Sheets não conecta:**
1. Verifique se as APIs estão habilitadas
2. Confirme se as credenciais estão corretas no secrets
3. Verifique se o service account tem acesso às planilhas

### **Deploy falha:**
1. Certifique-se que todas as dependências estão no requirements.txt
2. Verifique se não há arquivos grandes no repositório
3. Confirme que os secrets estão configurados corretamente

### **Performance lenta:**
1. O primeiro acesso pode ser mais lento (inicialização)
2. Cache do Streamlit otimiza acessos subsequentes
3. Google Sheets tem limites de API (normalmente suficientes)

---

*Desenvolvido com ❤️ usando Streamlit, Python e Google Sheets* 