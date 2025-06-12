import streamlit as st
import gspread
import pandas as pd
from datetime import datetime
import json
from google.oauth2.service_account import Credentials

class PortfolioManager:
    """
    Gerenciador de portfólios usando Google Sheets como backend
    """
    
    def __init__(self):
        self.scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        self.sheet_name = "Portfolio_History"
        self.client = None
        self.spreadsheet = None
    
    @st.cache_resource
    def get_google_sheets_client(_self):
        """
        Conecta com Google Sheets usando credenciais do Streamlit secrets
        """
        try:
            # Obtém credenciais do secrets.toml
            credentials_dict = st.secrets["gcp_service_account"]
            credentials = Credentials.from_service_account_info(
                credentials_dict, 
                scopes=_self.scopes
            )
            return gspread.authorize(credentials)
        except Exception as e:
            st.error(f"❌ Erro ao conectar Google Sheets: {e}")
            return None
    
    def get_spreadsheet(self):
        """
        Obtém ou cria a planilha principal
        """
        if not self.client:
            self.client = self.get_google_sheets_client()
            
        if not self.client:
            return None
            
        try:
            # Tenta abrir planilha existente
            self.spreadsheet = self.client.open(self.sheet_name)
            return self.spreadsheet
        except gspread.SpreadsheetNotFound:
            # Cria nova planilha
            st.info("📝 Criando nova planilha no Google Sheets...")
            self.spreadsheet = self.client.create(self.sheet_name)
            
            # Compartilha com o próprio email (opcional)
            try:
                email = st.secrets.get("admin_email", None)
                if email:
                    self.spreadsheet.share(email, perm_type='user', role='writer')
            except:
                pass  # Ignora se não conseguir compartilhar
                
            return self.spreadsheet
    
    def get_portfolio_names(self):
        """
        Retorna lista de nomes de portfólios salvos
        """
        spreadsheet = self.get_spreadsheet()
        if not spreadsheet:
            return []
            
        try:
            worksheets = [ws.title for ws in spreadsheet.worksheets()]
            # Remove worksheets de controle
            portfolios = [ws for ws in worksheets if not ws.startswith('_')]
            return sorted(portfolios)
        except Exception as e:
            st.error(f"❌ Erro ao listar portfólios: {e}")
            return []
    
    def save_portfolio(self, portfolio_name, df_portfolio, metadata=None):
        """
        Salva portfólio no Google Sheets
        """
        spreadsheet = self.get_spreadsheet()
        if not spreadsheet:
            return False
            
        try:
            # Prepara dados para salvar
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Adiciona colunas de controle
            df_to_save = df_portfolio.copy()
            df_to_save['upload_date'] = timestamp
            df_to_save['version'] = len(self.get_portfolio_history(portfolio_name)) + 1
            
            # Adiciona metadados se fornecidos
            if metadata:
                for key, value in metadata.items():
                    df_to_save[f'meta_{key}'] = value
            
            # Verifica se worksheet existe
            try:
                worksheet = spreadsheet.worksheet(portfolio_name)
            except gspread.WorksheetNotFound:
                # Cria novo worksheet
                worksheet = spreadsheet.add_worksheet(
                    title=portfolio_name, 
                    rows=1000, 
                    cols=20
                )
            
            # Adiciona headers se é o primeiro registro
            if worksheet.row_count <= 1 or not worksheet.get('A1'):
                headers = df_to_save.columns.tolist()
                worksheet.insert_row(headers, 1)
            
            # Adiciona dados
            values = df_to_save.values.tolist()
            worksheet.append_rows(values)
            
            st.success(f"✅ Portfólio '{portfolio_name}' salvo com sucesso!")
            return True
            
        except Exception as e:
            st.error(f"❌ Erro ao salvar portfólio: {e}")
            return False
    
    def load_portfolio(self, portfolio_name, version='latest'):
        """
        Carrega portfólio do Google Sheets
        """
        spreadsheet = self.get_spreadsheet()
        if not spreadsheet:
            return None
            
        try:
            worksheet = spreadsheet.worksheet(portfolio_name)
            data = worksheet.get_all_records()
            
            if not data:
                st.warning(f"⚠️ Portfólio '{portfolio_name}' está vazio")
                return None
            
            df = pd.DataFrame(data)
            
            # Filtra por versão se especificado
            if version != 'latest' and 'version' in df.columns:
                df = df[df['version'] == version]
            elif version == 'latest' and 'version' in df.columns:
                latest_version = df['version'].max()
                df = df[df['version'] == latest_version]
            
            # Remove colunas de controle para retornar dados limpos
            control_columns = ['upload_date', 'version'] + [col for col in df.columns if col.startswith('meta_')]
            df_clean = df.drop(columns=[col for col in control_columns if col in df.columns])
            
            return df_clean
            
        except gspread.WorksheetNotFound:
            st.warning(f"⚠️ Portfólio '{portfolio_name}' não encontrado")
            return None
        except Exception as e:
            st.error(f"❌ Erro ao carregar portfólio: {e}")
            return None
    
    def get_portfolio_history(self, portfolio_name):
        """
        Retorna histórico de versões de um portfólio
        """
        spreadsheet = self.get_spreadsheet()
        if not spreadsheet:
            return []
            
        try:
            worksheet = spreadsheet.worksheet(portfolio_name)
            data = worksheet.get_all_records()
            
            if not data:
                return []
            
            df = pd.DataFrame(data)
            
            if 'upload_date' not in df.columns:
                return []
            
            # Agrupa por versão/data
            history = []
            for _, group in df.groupby(['version', 'upload_date']):
                history.append({
                    'version': group['version'].iloc[0],
                    'date': group['upload_date'].iloc[0],
                    'assets_count': len(group),
                    'total_quantity': group['Quantidade'].sum() if 'Quantidade' in group.columns else 0
                })
            
            return sorted(history, key=lambda x: x['version'], reverse=True)
            
        except Exception as e:
            st.error(f"❌ Erro ao obter histórico: {e}")
            return []
    
    def delete_portfolio(self, portfolio_name):
        """
        Remove um portfólio completamente
        """
        spreadsheet = self.get_spreadsheet()
        if not spreadsheet:
            return False
            
        try:
            worksheet = spreadsheet.worksheet(portfolio_name)
            spreadsheet.del_worksheet(worksheet)
            st.success(f"✅ Portfólio '{portfolio_name}' removido com sucesso!")
            return True
        except Exception as e:
            st.error(f"❌ Erro ao remover portfólio: {e}")
            return False
    
    def compare_portfolios(self, portfolio_name, version1, version2):
        """
        Compara duas versões de um portfólio
        """
        try:
            df1 = self.load_portfolio_version(portfolio_name, version1)
            df2 = self.load_portfolio_version(portfolio_name, version2)
            
            if df1 is None or df2 is None:
                return None
            
            # Realiza comparação básica
            changes = {
                'added': [],
                'removed': [],
                'modified': []
            }
            
            set1 = set(df1['Ativo'].values)
            set2 = set(df2['Ativo'].values)
            
            changes['added'] = list(set2 - set1)
            changes['removed'] = list(set1 - set2)
            
            # Verifica modificações nas quantidades
            common_assets = set1 & set2
            for asset in common_assets:
                qty1 = df1[df1['Ativo'] == asset]['Quantidade'].iloc[0]
                qty2 = df2[df2['Ativo'] == asset]['Quantidade'].iloc[0]
                if qty1 != qty2:
                    changes['modified'].append({
                        'asset': asset,
                        'old_qty': qty1,
                        'new_qty': qty2,
                        'change': qty2 - qty1
                    })
            
            return changes
            
        except Exception as e:
            st.error(f"❌ Erro ao comparar portfólios: {e}")
            return None
    
    def load_portfolio_version(self, portfolio_name, version):
        """
        Carrega uma versão específica do portfólio
        """
        spreadsheet = self.get_spreadsheet()
        if not spreadsheet:
            return None
            
        try:
            worksheet = spreadsheet.worksheet(portfolio_name)
            data = worksheet.get_all_records()
            
            if not data:
                return None
            
            df = pd.DataFrame(data)
            
            if 'version' in df.columns:
                df_version = df[df['version'] == version]
                if df_version.empty:
                    return None
                
                # Remove colunas de controle
                control_columns = ['upload_date', 'version'] + [col for col in df.columns if col.startswith('meta_')]
                df_clean = df_version.drop(columns=[col for col in control_columns if col in df.columns])
                return df_clean
            
            return None
            
        except Exception as e:
            st.error(f"❌ Erro ao carregar versão específica: {e}")
            return None 