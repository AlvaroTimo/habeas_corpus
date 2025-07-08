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

import os
import requests

import time
import random

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def configurar_driver():
    opts = Options()

    opts.add_argument(
        "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36"
    )

    opts.add_argument("--disable-search-engine-choice-screen")
    opts.add_argument('--headless=new')

    prefs = {
        "download_restrictions": 3,
    }
    opts.add_experimental_option("prefs", prefs)

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts)
    return driver

def ir_a_decisiones(driver, url):
    driver.get(url)
    try:
        logging.info(f"Esperando botón de decisiones en: {url}")
        decisiones_btn = WebDriverWait(driver, 100).until(
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
        documentos = WebDriverWait(driver, 100).until(
            EC.presence_of_all_elements_located((
                By.XPATH,
                "//div[@id='idDivDecisoes']//div[@class='clsDecisoesMonocraticasBlocoInterno' or @class='clsDecisoesIntTeorRevistaLinhaTodosDocumentos']"
            ))

            #EC.presence_of_all_elements_located((
            #    By.XPATH,
            #    "//div[@id='idDivDecisoes']//div[@class='clsDecisoesIntTeorRevistaLinhaTodosDocumentos']"
            #))
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
    df = pd.read_csv(
        "dataset_limpio_final.csv",
        header=0,
        on_bad_lines='skip',
        na_values=["", " ", "  "]
    )

    ultimo_indice_descargado = 34619

    df_stj = df[
        (df.index >= ultimo_indice_descargado) &
        df["link"].notna() &
        df["link"].str.startswith("https://processo.stj.jus.br")
    ]

    indices_stj = df_stj.index.tolist()
    links_stj = df_stj["link"].tolist()

    total_indices = len(links_stj)

    logging.info(f"Se encontraron {len(links_stj)} links STJ en el CSV.")

    driver = configurar_driver()

    all_extracted_urls = []

    wait_time = random.uniform(1, 3)
    for idx, url in enumerate(links_stj, 1):
        try:
            logging.info(f"Procesando link con indice {idx + ultimo_indice_descargado - 1}/{total_indices + ultimo_indice_descargado - 1}: {url}")

            if ir_a_decisiones(driver, url):
                documentos = obtener_documentos(driver)
                urls_extraidas = extraer_urls(documentos)

                #Aqui podemos agregar una nueva columna al dataset con las urls?? (luego borramos todas las filas que no tengan urls)
                numero_documento = 0
                for url_extraida in urls_extraidas:
                    driver.execute_script(
                        "window.open(arguments[0], '_blank');", url_extraida
                    )
                    driver.switch_to.window(driver.window_handles[1])

                    url_sin_iframe = WebDriverWait(driver, 100).until(
                        EC.presence_of_element_located((By.XPATH, "//div[@align='right']//a"))
                    ).get_attribute("href")

                    driver.close()
                    
                    driver.switch_to.window(driver.window_handles[0])

                    pdf = requests.get(
                        url_sin_iframe,
                        stream=True
                    )

                    if pdf.status_code == 200:
                        with open(f"./pdfs_stj/documento_{indices_stj[idx-1]}_{numero_documento}.pdf", "wb") as f:
                            f.write(pdf.content)
                        logging.info(f"PDF_{indices_stj[idx-1]}_{numero_documento} descargado correctamente.")
                        numero_documento += 1
                    else:
                        logging.info(f"Error al descargar el PDF_{indices_stj[idx-1]}_{numero_documento}. Código de estado: {pdf.status_code}")

                    driver.switch_to.window(driver.window_handles[0])
                all_extracted_urls.extend(urls_extraidas)
            else:
                logging.error(f"No se pudo acceder a la pestaña de decisiones en: {url}")
            
            wait_time = random.uniform(1, 3)
            time.sleep(wait_time)

            if idx % 50 == 0:
                driver.quit()
                time.sleep(wait_time)
                driver = configurar_driver()

        except Exception as e:
            logging.error(e)
            with open("errores.txt", "a") as archivo:
                archivo.write(f"{indices_stj[idx-1]}\n")

            driver.quit()
            time.sleep(wait_time)
            driver = configurar_driver()


    driver.quit()
    logging.info("Driver cerrado correctamente.")

    if all_extracted_urls:
        df_out = pd.DataFrame({"urls_documentos": all_extracted_urls})
        df_out.to_csv("urls_documentos_stj.csv", index=False)
        logging.info("Se guardaron las URLs extraídas en urls_documentos_stj.csv.")
    else:
        logging.info("No se extrajo ninguna URL.")

if __name__ == "__main__":
    main()
