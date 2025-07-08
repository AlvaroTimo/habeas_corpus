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
    prefs = {"download_restrictions": 3}
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


def leer_errores(path_errores):
    if not os.path.exists(path_errores):
        logging.info("No existe archivo de errores. Nada que reintentar.")
        return []
    with open(path_errores, "r") as f:
        indices = [int(line.strip()) for line in f if line.strip().isdigit()]
    return indices


def agregar_error(path_errores, indice):
    with open(path_errores, "a") as f:
        f.write(f"{indice}\n")
    logging.info(f"Se agregó el índice {indice} a {path_errores}")


def main():
    path_errores = "errores.txt"
    path_errores_restantes = "errores_restantes.txt"

    # Borra archivo de errores_restantes si existe para empezar limpio
    if os.path.exists(path_errores_restantes):
        os.remove(path_errores_restantes)

    errores_indices = leer_errores(path_errores)

    if not errores_indices:
        logging.info("No hay errores que reintentar. Fin.")
        return

    df = pd.read_csv(
        "dataset_limpio_final.csv",
        header=0,
        on_bad_lines='skip',
        na_values=["", " ", "  "]
    )

    # Filtra solo filas con esos índices
    df_errores = df.loc[errores_indices]
    df_errores = df_errores[
        df_errores["link"].notna() &
        df_errores["link"].str.startswith("https://processo.stj.jus.br")
    ]

    if df_errores.empty:
        logging.info("No se encontraron filas válidas para reintentar.")
        return

    driver = configurar_driver()

    all_extracted = []

    for idx, row in df_errores.iterrows():
        link = row["link"]
        try:
            logging.info(f"Reintentando índice {idx}: {link}")
            if ir_a_decisiones(driver, link):
                documentos = obtener_documentos(driver)
                urls_extraidas = extraer_urls(documentos)

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

                    pdf = requests.get(url_sin_iframe, stream=True)
                    if pdf.status_code == 200:
                        pdf_path = f"./pdfs_stj/documento_{idx}_{numero_documento}.pdf"
                        with open(pdf_path, "wb") as f:
                            f.write(pdf.content)
                        logging.info(f"PDF_{idx}_{numero_documento} descargado correctamente.")
                        numero_documento += 1
                    else:
                        logging.warning(f"Error al descargar el PDF_{idx}_{numero_documento}. Status: {pdf.status_code}")

                all_extracted.append({
                    "indice": idx,
                    "urls_documentos": ";".join(urls_extraidas) if urls_extraidas else None
                })

            else:
                logging.error(f"No se pudo acceder a la pestaña de decisiones en {link}")
                agregar_error(path_errores_restantes, idx)

            time.sleep(random.uniform(1, 3))

        except Exception as e:
            logging.error(f"Error procesando índice {idx}: {e}")
            agregar_error(path_errores_restantes, idx)

            driver.quit()
            time.sleep(random.uniform(1, 3))
            driver = configurar_driver()

    driver.quit()

    if all_extracted:
        df_out = pd.DataFrame(all_extracted)
        df_out.to_csv("urls_documentos_stj_retry.csv", index=False)
        logging.info("Se guardaron las URLs extraídas en urls_documentos_stj_retry.csv.")
    else:
        logging.info("No se extrajeron URLs en este intento.")


if __name__ == "__main__":
    main()
