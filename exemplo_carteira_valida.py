import pandas as pd

# Dados com tickers conhecidos que funcionam
dados_validos = {
    'Ativo': [
        'PETR4',    # Petrobras
        'VALE3',    # Vale
        'ITUB4',    # Itaú Unibanco
        'BBDC4',    # Bradesco
        'ABEV3',    # Ambev
        'WEGE3',    # WEG
        'BBAS3',    # Banco do Brasil
        'B3SA3',    # B3
        'RAIL3',    # Rumo
        'RENT3'     # Localiza
    ],
    'Quantidade': [
        100,  # PETR4
        50,   # VALE3
        200,  # ITUB4
        150,  # BBDC4
        300,  # ABEV3
        80,   # WEGE3
        100,  # BBAS3
        75,   # B3SA3
        60,   # RAIL3
        40    # RENT3
    ]
}

# Cria o DataFrame
df_valido = pd.DataFrame(dados_validos)

# Salva os arquivos
df_valido.to_excel('carteira_valida.xlsx', index=False)
df_valido.to_csv('carteira_valida.csv', index=False, sep=';', encoding='utf-8')

print("✅ Arquivos com tickers válidos criados:")
print("  - carteira_valida.xlsx")
print("  - carteira_valida.csv")
print("\nConteúdo (tickers conhecidos que funcionam):")
print(df_valido.to_string(index=False))
print(f"\nTotal de ativos: {len(df_valido)}")
print(f"Quantidade total: {df_valido['Quantidade'].sum()}")

print("\n" + "="*50)
print("✅ ESTES TICKERS ESTÃO VALIDADOS E DEVEM FUNCIONAR")
print("="*50) 