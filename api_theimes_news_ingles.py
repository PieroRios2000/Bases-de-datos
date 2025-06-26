from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

# Configuración inicial
fecha_inicio = datetime.strptime("20250101", "%Y%m%d")
fecha_fin = datetime.strptime("20250601", "%Y%m%d")
original_url = 'https://www.thetimes.com/'
resultados = []

WAYBACK_TIMEOUT = 30
SNAPSHOT_TIMEOUT = 30
RETRIES = 3
SLEEP_BETWEEN_DAYS = 2

fecha = fecha_inicio
while fecha <= fecha_fin:
    fecha_str = fecha.strftime("%Y%m%d")
    wayback_api = f'https://archive.org/wayback/available?url={original_url}&timestamp={fecha_str}'
    success = False
    for intento in range(RETRIES):
        try:
            res = requests.get(wayback_api, timeout=WAYBACK_TIMEOUT)
            data = res.json()
            if 'archived_snapshots' in data and data['archived_snapshots']:
                snapshot_url = data['archived_snapshots']['closest']['url']
                if snapshot_url.startswith("http://"):
                    snapshot_url = snapshot_url.replace("http://", "https://")
                try:
                    page = requests.get(snapshot_url, timeout=SNAPSHOT_TIMEOUT)
                    soup = BeautifulSoup(page.content, 'html.parser')

                    # Adaptar esta parte a la estructura de The Times
                    titulares = soup.find_all(['h1', 'h2', 'h3'])
                    for t in titulares:
                        texto = t.get_text(strip=True)
                        if texto:
                            resultados.append({
                                "fecha": fecha_str,
                                "titular": texto,
                                "url_archivo": snapshot_url
                            })
                    success = True
                    break
                except Exception as e:
                    print(f"Error accediendo a {snapshot_url} (intento {intento+1}): {e}")
            else:
                print(f"No hay snapshot para {fecha_str}")
                success = True
                break
        except Exception as e:
            print(f"Error consultando Wayback para {fecha_str} (intento {intento+1}): {e}")
            time.sleep(3)
    if not success:
        print(f"Fallo persistente en {fecha_str}, se omite el día.")
    time.sleep(SLEEP_BETWEEN_DAYS)
    fecha += timedelta(days=1)

# Resultados
df_titulares = pd.DataFrame(resultados)
print(df_titulares.head())
print(f"Total de titulares recopilados: {len(df_titulares)}")
df_titulares.to_csv("thetimes_2025.csv", index=False)
