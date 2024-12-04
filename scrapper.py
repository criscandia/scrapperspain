import os
from datetime import datetime
import pandas as pd
import requests
import random
import time
import logging

# Configuración del log de depuración
logging.basicConfig(filename="script.log", level=logging.DEBUG)


def get_proxies():
    response = requests.get("https://free-proxy-list.net/")
    html = response.text
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    proxies = []
    for row in soup.find_all("tr"):
        cols = row.find_all("td")
        if len(cols) > 6:
            proxy = cols[0].text + ":" + cols[1].text
            proxies.append(proxy)
    return proxies


def verificar_proxy(proxy):
    try:
        response = requests.get(
            "http://www.google.com",
            proxies={"http": f"http://{proxy}", "https": f"http://{proxy}"},
        )
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException:
        return False


def search_linkedin_profiles(company_name, roles):
    linkedin_profiles = []
    proxies = get_proxies()
    intentos = 0
    tiempo_inicial = datetime.now()
    for role in roles:
        query = f'site:linkedin.com "{role}" "{company_name}"'
        proxy = random.choice(proxies)
        if verificar_proxy(proxy):  # Cambiar a verificar_proxy
            print(f"Utilizando proxy: {proxy}")
            intentos += 1
            while True:
                try:
                    url = f"http://www.google.com/search?q={query}"
                    headers = {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
                    }
                    response = requests.get(
                        url,
                        headers=headers,
                        proxies={"http": f"http://{proxy}", "https": f"http://{proxy}"},
                    )
                    response.raise_for_status()
                    print(f"Estado de conexión: {response.status_code}")
                    html = response.text
                    from bs4 import BeautifulSoup

                    soup = BeautifulSoup(html, "html.parser")
                    links = soup.find_all("a")
                    for link in links:
                        href = link.get("href")
                        if href and "linkedin.com/in/" in href:
                            linkedin_profiles.append(href)
                            print(f"Encontrado: {href}")
                    break
                except requests.exceptions.RequestException as e:
                    # Si la solicitud falla, esperar 30 segundos antes de reintentar
                    print(f"Error buscando LinkedIn para {company_name} - {role}: {e}")
                    print(f"Estado de conexión: Error")
                    time.sleep(30)
        tiempo_transcurrido = (datetime.now() - tiempo_inicial).total_seconds()
        print(f"Tiempo transcurrido: {tiempo_transcurrido} segundos")
        time.sleep(5)  # agregar un retraso de 5 segundos
    print(f"Intentos realizados: {intentos}")
    print(f"Datos encontrados: {len(linkedin_profiles)}")
    return linkedin_profiles


# Configuración de los roles a buscar y los datos del archivo
roles_to_search = ["Manager", "Director", "CTO", "CEO"]
file_path = "Acelera Pyme - Digitalizadores_v1.xlsx"  # Actualiza con la ruta de tu archivo Excel

# Leer los datos del archivo Excel
sheet_data = pd.read_excel(file_path, sheet_name="Acelera Pyme - Digitalizadores ")
companies = sheet_data[["Nombre", "URL"]].dropna()

# Crear un DataFrame para almacenar los resultados
linkedin_results = []

# Iterar por cada empresa y buscar perfiles
for _, row in companies.iterrows():
    company_name = row["Nombre"]
    company_url = row["URL"]
    profiles = search_linkedin_profiles(company_name, roles_to_search)
    linkedin_results.append(
        {
            "Nombre": company_name,
            "URL Empresa": company_url,
            "Perfiles LinkedIn": "; ".join(profiles) if profiles else "No encontrado",
        }
    )

# Convertir los resultados a un DataFrame
linkedin_df = pd.DataFrame(linkedin_results)

# Agregar la fecha y hora actual al nombre del archivo
output_file = f"linkedin_profiles_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
output_path = os.path.join(os.getcwd(), output_file)

# Guardar los resultados en un archivo CSV
linkedin_df.to_csv(output_path, index=False)

print(f"Archivo CSV generado: {output_path}")
