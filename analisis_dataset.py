import pandas as pd

# Nos falta arreglar las columnas en las que la fecha no sea una fecha entonces, si la siguiente columna es una fecha,
# fusionamos en asunto todas las columnas hasta llegar a la fecha 

df = pd.read_csv(
    "dataset_limpio.csv",
    header=0,
    on_bad_lines='skip',
    na_values=["", " ", "  "]
)

df.insert(0, "indice", df.index)
df["link"] = df["link"].str.strip()
df = df.drop_duplicates(subset=["link"])

df = df.dropna(axis=1, how='all')
print(f"Shape después de eliminar columnas vacías: {df.shape}")

# Tal vez podemos dropear los links que son iguales

#print("\nValores faltantes por columna (ordenado):\n")
#print(df.isna().sum().sort_values(ascending=False))

# Contar NaN por columna
""" nan_counts = df.isna().sum()

print("Imprimiendo nan counts",nan_counts)

print("\nColumnas con más de 80,000 valores vacíos:")
print(nan_counts[nan_counts > 80000])

df = df.loc[:, nan_counts <= 80000]
print(f"\nShape después de eliminar columnas con >80,000 NaN: {df.shape}") """

df.to_csv("dataset_limpio_final.csv", encoding='utf-8')
print("CSV final guardado")

""" print("\nValores faltantes por columna (ordenado) despues de eliminar columnas:\n")
print(df.isna().sum().sort_values(ascending=False))

# Lista de columnas que quieres inspeccionar
cols_a_ver = [
    'redator acórdão',
    'observações',
    'tipo penal.1',
    'tema.1'
]

# Mostrar las primeras 50 filas de esas columnas
print(df[cols_a_ver].head(50)) """