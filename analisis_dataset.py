import pandas as pd

df = pd.read_csv(
    "dataset_limpio.csv",
    header=0,
    on_bad_lines='skip',
    na_values=["", " ", "  "]
)

#Agregamos indices
df.insert(0, "indice", df.index)

#Limpiamos espacios antes y despues de los links para luego eliminar los repetidos
df["link"] = df["link"].str.strip()
df = df.drop_duplicates(subset=["link"])

# Eliminar columnas completamente vacías
df = df.dropna(axis=1, how='all')
print(f"Shape después de eliminar columnas vacías: {df.shape}")

#print("\nValores faltantes por columna (ordenado):\n")
#print(df.isna().sum().sort_values(ascending=False))

# Contar NaN por columna
""" nan_counts = df.isna().sum()

print("Imprimiendo nan counts",nan_counts)

print("\nColumnas con más de 80,000 valores vacíos:")
print(nan_counts[nan_counts > 80000])

df = df.loc[:, nan_counts <= 80000]
print(f"\nShape después de eliminar columnas con >80,000 NaN: {df.shape}") """

# Guardar el CSV limpio actualizado
df.to_csv("dataset_limpio_final.csv", index=False, encoding='utf-8')
print("¡CSV final guardado con columnas filtradas!")

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