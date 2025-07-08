import os
import time
import random
from pathlib import Path

import pandas as pd
import logging

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from selenium.common.exceptions import TimeoutException, NoSuchElementException

from webdriver_manager.chrome import ChromeDriverManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def configurar_driver(download_path):
    try:
        opts = Options()
        opts.add_argument(
            "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36"
        )
        opts.add_argument("--disable-search-engine-choice-screen")
        opts.add_argument("--disable-blink-features=AutomationControlled")
        opts.add_argument("--incognito")
        opts.add_argument("--headless=new")

        prefs = {
            "download.default_directory": download_path,
            "plugins.always_open_pdf_externally": True
        }
        opts.add_experimental_option("prefs", prefs)

        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts)

        logging.info("Driver configurado correctamente")
        return driver
    except Exception as e:
        logging.error(f"Error al configurar el driver: {e}")


def habilitar_descargas_driver(driver, download_path):
    try:
        driver.command_executor._commands["send_command"] = (
            "POST",
            "/session/$sessionId/chromium/send_command"
        )
        params = {
            'cmd': 'Page.setDownloadBehavior',
            'params': {
                'behavior': 'allow',
                'downloadPath': download_path
            }
        }
        driver.execute("send_command", params)

        logging.info("Se habilitaron las descargas del driver en modo headless")
    except Exception as e:
        logging.error(f"No se pudieron activar las descargas del driver: {e}")


def aceptar_cookies(driver, url):
    driver.get(url)

    try:
        boton_cookies = WebDriverWait(driver, 3).until(
            EC.presence_of_element_located((By.XPATH, "//button[@id='acceptCookies']"))
        )
        boton_cookies.click()

        WebDriverWait(driver, 3).until(
            EC.invisibility_of_element_located((By.XPATH, "//button[@id='acceptCookies']"))
        )

        logging.info("Se aceptaron las cookies exitosamente")
    except:
        logging.warning("Cookies ya aceptadas o no encontradas.")


def obtener_documentos(driver):
    try:
        andamentos_docs = WebDriverWait(driver, 5).until(
            EC.presence_of_all_elements_located((By.XPATH, "//div[contains(@class,'andamento-docs')]//a[contains(@class,'andamento-doc')]"))
        )
        andamentos_docs = [
            el for el in andamentos_docs
            if el.text.strip().lower() == "decisão monocrática"
        ]
        logging.info(f"Se obtuvieron {len(andamentos_docs)} documentos exitosamente.")
        return andamentos_docs

    except:
        logging.warning("No se pudieron obtener documentos.")
        return []


def renombrar_documento(download_path, nuevo_nombre, timeout=60):
    try:
        download_dir = Path(download_path)
        archivo_final = download_dir / "downloadPeca.pdf"
        archivo_temporal = download_dir / "downloadPeca.pdf.crdownload"
        ruta_nueva = archivo_final.with_name(nuevo_nombre)

        tiempo_inicio = time.time()

        while True:
            if archivo_final.exists() and not archivo_temporal.exists():
                logging.info(f"Documento {nuevo_nombre} descargado exitosamente")
                break

            if time.time() - tiempo_inicio > timeout:
                logging.warning(f"No se pudo descargar el documento {nuevo_nombre}")
                raise TimeoutError(
                    f"La descarga de {archivo_final.name} no terminó tras {timeout} segundos."
                )
            
            time.sleep(1)

        archivo_final.rename(ruta_nueva)
        logging.info("Se renombró el archivo descargado.")
        return True

    except Exception as e:
        logging.error(f"Error al renombrar el documento {nuevo_nombre}: {e}")
        return False


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
    path_errores = "errores_stf.txt"
    path_errores_restantes = "errores_stf_restantes.txt"

    # Borrar errores_stf_restantes.txt para empezar limpio
    if os.path.exists(path_errores_restantes):
        os.remove(path_errores_restantes)

    errores_indices = leer_errores(path_errores)

    df = pd.read_csv(
        "dataset_limpio_final.csv",
        header=0,
        on_bad_lines='skip',
        na_values=["", " ", "  "]
    )

    if errores_indices:
        # Usar errores como filtro
        df_stf = df.loc[errores_indices]
        df_stf = df_stf[
            df_stf["link"].notna() &
            df_stf["link"].str.startswith("https://portal.stf.jus.br/")
        ]
        logging.info(f"Reintentando {len(df_stf)} links desde archivo de errores.")
    else:
        # Ejecución normal
        ultimo_indice_descargado = 804
        df_stf = df[
            (df.index >= ultimo_indice_descargado) &
            df["link"].notna() &
            df["link"].str.startswith("https://portal.stf.jus.br/")
        ]
        logging.info(f"Se encontraron {len(df_stf)} links STF en el CSV.")

    if df_stf.empty:
        logging.info("No hay links válidos para procesar.")
        return

    indices_stf = df_stf.index.tolist()
    links_stf = df_stf["link"].tolist()

    download_path = "/home/alvaro/Documentos/FGV/pdfs_stf"
    driver = configurar_driver(download_path)
    habilitar_descargas_driver(driver, download_path)

    wait_time = random.uniform(1, 3)

    for idx, url in enumerate(links_stf, 1):
        indice_real = indices_stf[idx-1]
        try:
            logging.info(f"Procesando índice {indice_real}: {url}")
            aceptar_cookies(driver, url)

            andamentos_docs = obtener_documentos(driver)
            actions = ActionChains(driver)

            numero_documento = 0
            for andamento_doc in andamentos_docs:
                actions.move_to_element(andamento_doc).perform()
                andamento_doc_url = andamento_doc.get_attribute('href')
                logging.info(f"Se extrajo esta url: {andamento_doc_url}")

                driver.execute_script(
                    "window.open(arguments[0], '_blank');", andamento_doc_url
                )
                driver.switch_to.window(driver.window_handles[-1])

                nombre_archivo = f"documento_{indice_real}_{numero_documento}.pdf"
                numero_documento += 1

                resultado = renombrar_documento(download_path, nombre_archivo)

                driver.close()
                driver.switch_to.window(driver.window_handles[0])

                if not resultado:
                    raise Exception("Error al renombrar documento.")

            time.sleep(wait_time)

            if idx % 50 == 0:
                logging.info("Reiniciando driver...")
                driver.quit()
                time.sleep(wait_time)
                driver = configurar_driver(download_path)
                habilitar_descargas_driver(driver, download_path)

        except Exception as e:
            logging.error(f"Error procesando índice {indice_real}: {e}")
            agregar_error(path_errores_restantes, indice_real)

            driver.quit()
            time.sleep(wait_time)
            driver = configurar_driver(download_path)
            habilitar_descargas_driver(driver, download_path)

    driver.quit()
    logging.info("Driver cerrado exitosamente.")


if __name__ == "__main__":
    main()
