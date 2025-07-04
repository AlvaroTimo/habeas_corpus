import requests

import random
from selenium import webdriver
from time import sleep
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

opts = Options()
opts.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36")
opts.add_argument("--disable-search-engine-choice-screen")

#Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36

prefs = {"download.default_directory" : "/home/alvaro/Documentos/FGV/pdfs"}
opts.add_experimental_option("prefs",prefs)

driver = webdriver.Chrome(service = Service(ChromeDriverManager().install()), options=opts)

application/pdf

#CODIGO PROVISIONAL PARA LA URL DE PRUEBA
url_stj = "https://portal.stf.jus.br/processos/detalhe.asp?incidente=6507160"

# Voy a la pagina que requiero
driver.get(url_stj)

sleep(10)