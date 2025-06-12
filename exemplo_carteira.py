import pandas as pd

# Dados de exemplo de uma carteira diversificada
dados_exemplo = {
    'Ativo': [
        'PETR4',    # Petrobras
        'VALE3',    # Vale
        'ITUB4',    # Itaú Unibanco
        'BBDC4',    # Bradesco
        'ABEV3',    # Ambev
        'WEGE3',    # WEG
        'MGLU3',    # Magazine Luiza
        'BBAS3',    # Banco do Brasil
        'CPLE6',    # Copel
        'TAEE11'    # Taesa
    ],
    'Quantidade': [
        100,  # PETR4
        50,   # VALE3
        200,  # ITUB4
        150,  # BBDC4
        300,  # ABEV3
        80,   # WEGE3
        120,  # MGLU3
        100,  # BBAS3
        75,   # CPLE6
        60    # TAEE11
    ]
}

# Cria o DataFrame
df_exemplo = pd.DataFrame(dados_exemplo)

# Salva a planilha de exemplo
df_exemplo.to_excel('exemplo_carteira.xlsx', index=False)

print("✅ Planilha de exemplo criada: exemplo_carteira.xlsx")
print("\nConteúdo da planilha:")
print(df_exemplo.to_string(index=False))
print(f"\nTotal de ativos: {len(df_exemplo)}")
print(f"Quantidade total: {df_exemplo['Quantidade'].sum()}") 