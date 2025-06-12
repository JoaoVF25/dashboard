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

# Salva os arquivos de exemplo em diferentes formatos
# CSV com separador ponto e vírgula (padrão brasileiro)
df_exemplo.to_csv('exemplo_carteira.csv', index=False, sep=';', encoding='utf-8')

# CSV com separador vírgula (padrão internacional)
df_exemplo.to_csv('exemplo_carteira_virgula.csv', index=False, sep=',', encoding='utf-8')

print("✅ Arquivos CSV de exemplo criados:")
print("  - exemplo_carteira.csv (separador: ;)")
print("  - exemplo_carteira_virgula.csv (separador: ,)")
print("\nConteúdo dos arquivos:")
print(df_exemplo.to_string(index=False))
print(f"\nTotal de ativos: {len(df_exemplo)}")
print(f"Quantidade total: {df_exemplo['Quantidade'].sum()}")

# Também mostra como ficariam os CSVs
print("\n" + "="*50)
print("PREVIEW CSV com separador ';':")
print("="*50)
print("Ativo;Quantidade")
for _, row in df_exemplo.iterrows():
    print(f"{row['Ativo']};{row['Quantidade']}")

print("\n" + "="*50)
print("PREVIEW CSV com separador ',':")
print("="*50)
print("Ativo,Quantidade")
for _, row in df_exemplo.iterrows():
    print(f"{row['Ativo']},{row['Quantidade']}") 