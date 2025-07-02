import re
import logging
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

# Para descargar los datasets
import os
import requests

#Libreria temporal para hcaer pruebas
import time

# Configurar logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def configurar_driver():
    opts = Options()
    opts.add_argument(
        "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36"
    )
    opts.add_argument("--disable-search-engine-choice-screen")
    prefs = {"download.default_directory": "/home/alvaro/Documentos/FGV/pdfs"}
    opts.add_experimental_option("prefs", prefs)

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts)
    return driver

def ir_a_decisiones(driver, url):
    driver.get(url)

    try:
        logging.info(f"Esperando botón de decisiones en: {url}")
        decisiones_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//span[@id='idSpanAbaDecisoes']"))
        )
        decisiones_btn.click()
        logging.info("Se hizo clic en la pestaña de Decisiones.")
    except TimeoutException:
        logging.error("No se encontró el botón de decisiones.")
        return False
    return True

def obtener_documentos(driver):
    try:
        documentos = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((
                By.XPATH,
                "//div[@id='idDivDecisoes']//div[@class='clsDecisoesMonocraticasBlocoInterno' or @class='clsDecisoesIntTeorRevistaLinhaTodosDocumentos']"
            ))
        )
        logging.info(f"Se encontraron {len(documentos)} documentos.")
        return documentos
    except TimeoutException:
        logging.warning("No se encontraron documentos en el tiempo esperado.")
        return []

def extraer_urls(documentos):
    urls = []
    base_url = "https://processo.stj.jus.br"

    for doc in documentos:
        try:
            link_element = doc.find_element(By.XPATH, ".//a")
            onclick_attr = link_element.get_attribute("onclick")
            match = re.search(r"abrirDocumento\('([^']+)'", onclick_attr)
            if match:
                url_completa = base_url + match.group(1)
                urls.append(url_completa)
                logging.info(f"URL extraída: {url_completa}")
            else:
                logging.warning("No se pudo extraer la URL del documento.")
        except NoSuchElementException:
            logging.warning("Documento sin enlace encontrado.")
    return urls

def main():
    # Leer CSV
    df = pd.read_csv(
        "dataset_limpio_final.csv",
        header=0,
        on_bad_lines='skip',
        na_values=["", " ", "  "]
    )

    # Filtrar solo los links STJ
    df_stj = df[
        df["link"].notna() & df["link"].str.startswith("https://processo.stj.jus.br")
    ]

    links_stj = df_stj["link"].tolist()

    logging.info(f"Se encontraron {len(links_stj)} links STJ en el CSV.")

    driver = configurar_driver()

    all_extracted_urls = []

    try:
        for idx, url in enumerate(links_stj, 1):
            logging.info(f"Procesando link {idx}/{len(links_stj)}: {url}")

            if ir_a_decisiones(driver, url):
                documentos = obtener_documentos(driver)
                urls_extraidas = extraer_urls(documentos)

                #Aqui podemos agregar una nueva columna al dataset con las urls?? (luego borramos todas las filas que no tengan urls)
                #Contador temporal, arreglar, porque sobreescribira si lo aplicamos a todo el dataset
                
                contador = 0
                for url_extraida in urls_extraidas:
                    driver.execute_script(
                        "window.open(arguments[0], '_blank');", url_extraida
                    )
                    driver.switch_to.window(driver.window_handles[1])
                    url_sin_iframe = driver.find_element("xpath","//div//a").get_attribute("href")
                    driver.close()
                    
                    driver.switch_to.window(driver.window_handles[0])

                    pdf = requests.get(url_sin_iframe)
                    if pdf.status_code == 200:
                        with open(f"documento_{contador}.pdf", "wb") as f:
                            f.write(pdf.content)
                        contador+=1
                        print("PDF descargado correctamente.")
                    else:
                        print(f"Error al descargar el PDF. Código de estado: {pdf.status_code}")


                    driver.switch_to.window(driver.window_handles[0])


                all_extracted_urls.extend(urls_extraidas)
            else:
                logging.error(f"No se pudo acceder a la pestaña de decisiones en: {url}")

            # break de prueba para cortar las descargas con la primera url
            break

    finally:
        driver.quit()
        logging.info("Driver cerrado correctamente.")

    # Opcional: guardar las URLs extraídas en CSV
    if all_extracted_urls:
        df_out = pd.DataFrame({"urls_documentos": all_extracted_urls})
        df_out.to_csv("urls_documentos_stj.csv", index=False)
        logging.info("Se guardaron las URLs extraídas en urls_documentos_stj.csv.")
    else:
        logging.info("No se extrajo ninguna URL.")

if __name__ == "__main__":
    main()
