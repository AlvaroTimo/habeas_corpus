with open('dataset.csv', 'r', encoding='utf-8', errors='ignore') as archivo:
    with open('dataset_limpio.csv', 'w', encoding='utf-8') as archivo_corregido:
        for linea in archivo:
            palabras = linea.strip().split(',')
            palabras_corregidas = []
            for palabra in palabras:
                palabra = palabra.replace('Ã‡', 'Ç')
                palabra = palabra.replace('Ãƒ', 'Ã')
                palabra = palabra.replace('Ã“', 'Ó')
                palabra = palabra.replace('â€“', '–')
                palabra = palabra.replace('Ã', 'Á')
                palabra = palabra.replace('Ã³', 'ó')
                palabra = palabra.replace('Ã§', 'ç')
                palabra = palabra.replace('Ã£', 'ã')
                palabra = palabra.replace('Ã£', 'ã')
                palabra = palabra.replace('Ã¡', 'á')
                palabra = palabra.replace('Ã‰', 'É')
                palabra = palabra.replace('Ã©', 'é')
                palabra = palabra.replace('Ãµ', 'õ')
                palabra = palabra.replace('Ãª', 'ê')
                palabra = palabra.replace('Ã•', 'Õ')
                palabra = palabra.replace('Ãº', 'ú')
                palabra = palabra.replace('"', '')

                try:
                    palabra = palabra.encode('latin1').decode('utf-8')
                except:
                    print("Estamos fallando en: ",palabra)
                    pass
                
                palabras_corregidas.append(palabra)
            linea_corregida = ','.join(palabras_corregidas) + '\n'
            archivo_corregido.write(linea_corregida)
