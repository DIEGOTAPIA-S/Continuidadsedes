import os
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.plugins import Draw, Search, LocateControl, Fullscreen
from shapely.geometry import Point, Polygon, shape, mapping
from fpdf import FPDF
from datetime import datetime
import matplotlib.pyplot as plt
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import tempfile
import unicodedata
import base64
from io import BytesIO
import pytz

# --- Configuración de la página ---
st.set_page_config(
    page_title="Continuidad del Negocio - Sedes",
    page_icon="assets/logo_colmedica.png",
    layout="wide",
    initial_sidebar_state="expanded"
)
st.title("🚨 Sistema de Gestión de Continuidad del Negocio - Sedes")

# --- Configuración de Mapas ---
TILES = {
    "MapLibre": {
        "url": "https://api.maptiler.com/maps/streets/{z}/{x}/{y}.png?key=dhEAG0dMVs2vmsaHdReR",
        "attr": '<a href="https://www.maptiler.com/copyright/" target="_blank">© MapTiler</a>'
    },
    "OpenStreetMap": {
        "url": "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        "attr": 'OpenStreetMap'
    }
}

# --- Sedes Fijas (con capacidad, descripción de ejemplo y AHORA con CIUDAD) ---
SEDES_FIJAS = {
    "Colmédica Belaire": {"direccion": "Centro Comercial Belaire Plaza, Cl. 153 #6-65, Bogotá", "coordenadas": [4.729454000113993, -74.02444216931787], "color": "blue", "icono": "hospital", "capacidad": "N° Usuarios/Colaboradores", "descripcion": "Información de sede", "ciudad": "Bogotá"},
    "Colmédica Bulevar Niza": {"direccion": "Centro Comercial Bulevar Niza, Av. Calle 58 #127-59, Bogotá", "coordenadas": [4.712693239837536, -74.07140074602322], "color": "blue", "icono": "hospital", "capacidad": "N° Usuarios/Colaboradores", "escripcion": "Información de sede", "ciudad": "Bogotá"},
    "Colmédica Calle 185": {"direccion": "Centro Comercial Santafé, Cl. 185 #45-03, Bogotá", "coordenadas": [4.763543959141223, -74.04612616931786], "color": "blue", "icono": "hospital", "capacidad": "N° Usuarios/Colaboradores", "descripcion": "Información de sede", "ciudad": "Bogotá"},
    "Colmédica Cedritos": {"direccion": "Edificio HHC, Cl. 140 #11-45, Bogotá", "coordenadas": [4.718879348342116, -74.03609218650581], "color": "blue", "icono": "hospital", "capacidad": "N° Usuarios/Colaboradores", "descripcion": "Información de sede", "ciudad": "Bogotá"},
    "Colmédica Chapinero": {"direccion": "Cr. 7 #52-53, Chapinero, Bogotá", "coordenadas": [4.640908410923512, -74.06373898409286], "color": "blue", "icono": "hospital", "capacidad": "N° Usuarios/Colaboradores", "descripcion": "Información de sede", "ciudad": "Bogotá"},
    "Colmédica Colina Campestre": {"direccion": "Centro Comercial Sendero de la Colina, Cl. 151 #54-15, Bogotá", "coordenadas": [4.73397996072128, -74.05613864417634], "color": "blue", "icono": "hospital", "capacidad": "N° Usuarios/Colaboradores", "descripcion": "Información de sede", "ciudad": "Bogotá"},
    "Colmédica Centro Médico Country Park": {"direccion": "Autopista Norte No 122 - 96, Bogotá", "coordenadas": [4.670067290638234, -74.05758327116473], "color": "blue", "icono": "hospital", "capacidad": "N° Usuarios/Colaboradores", "descripcion": "Información de sede", "ciudad": "Bogotá"},
    "Colmédica Metrópolis": {"direccion": "Centro Comercial Metrópolis, Av. Cra. 68 #75A-50, Bogotá", "coordenadas": [4.6812256618088615, -74.08315698409288], "color": "blue", "icono": "hospital", "capacidad": "N° Usuarios/Colaboradores", "descripcion": "Información de sede", "ciudad": "Bogotá"},
    "Colmédica Multiplaza": {"direccion": "Centro Comercial Multiplaza, Cl. 19A #72-57, Bogotá", "coordenadas": [4.652573284106405, -74.12629091534289], "color": "blue", "icono": "hospital", "capacidad": "N° Usuarios/Colaboradores", "descripcion": "Información de sede", "ciudad": "Bogotá"},
    "Colmédica Calle 93": {"direccion": "Cl. 93 #19-25 Piso 1, Chapinero,Bogotá", "coordenadas": [4.678423191882419, -74.05526357828552], "color": "blue", "icono": "hospital", "capacidad": "N° Usuarios/Colaboradores", "descripcion": "Información de sede", "ciudad": "Bogotá"},   
    "Colmédica Plaza Central": {"direccion": "Centro Comercial Plaza Central, Cra. 65 #11-50, Bogotá", "coordenadas": [4.633464230539147, -74.11621916981814], "color": "blue", "icono": "hospital", "capacidad": "N° Usuarios/Colaboradores", "descripcion": "Información de sede", "ciudad": "Bogotá"},
    "Colmédica Salitre Capital": {"direccion": "Capital Center II, Av. Cl. 26 #69C-03, Bogotá", "coordenadas": [4.660602588141229, -74.10864383068576], "color": "blue", "icono": "hospital", "capacidad": "N° Usuarios/Colaboradores", "descripcion": "Información de sede", "ciudad": "Bogotá"},
    "Colmédica Sede Administrativa": {"direccion": "Cl 63 #2875, Teusaquillo, Bogotá", "coordenadas": [4.652762, -74.076465], "color": "blue", "icono": "hospital", "capacidad": "N° Usuarios/Colaboradores", "Ddescripcion": " Información de sede", "ciudad": "Bogotá"},    
    "Colmédica Suba": {"direccion": "Alpaso Plaza, Av. Cl. 145 #103B-69, Bogotá", "coordenadas": [4.7499608085787575, -74.08737693178564], "color": "blue", "icono": "hospital", "capacidad": "N° Usuarios/Colaboradores", "descripcion": "Información de sede", "ciudad": "Bogotá"},
    "Colmédica Centro Médico Torre Santa Bárbara": {"direccion": "Autopista Norte No 122 - 96, Bogotá", "coordenadas": [4.70404406297091, -74.053790252428], "color": "blue", "icono": "hospital", "capacidad": "N° Usuarios/Colaboradores", "descripcion": "Información de sede", "ciudad": "Bogotá"},
    "Colmédica Unicentro Occidente": {"direccion": "Centro Comercial Unicentro Occidente, Cra. 111C #86-05, Bogotá", "coordenadas": [4.724354935414492, -74.11430016931786], "color": "blue", "icono": "hospital", "capacidad": "N° Usuarios/Colaboradores", "descripcion": "Información de sede", "ciudad": "Bogotá"},
    "Colmédica Usaquén": {"direccion": "Centro Comercial Usaquén, Cra. 7 #120-20, Bogotá", "coordenadas": [4.6985109910547695, -74.03076183068214], "color": "blue", "icono": "hospital", "capacidad": "N° Usuarios/Colaboradores", "descripcion": "Información de sede", "ciudad": "Bogotá"},
    "Centro Médico Colmédica Barranquilla Alto Prado": {"direccion": "Centro Comercial Cenco Altos del Prado, Calle 76 # 55-52, Barranquilla", "coordenadas": [11.004448920487901, -74.80367483068213], "color": "blue", "icono": "hospital", "capacidad": "N° Usuarios/Colaboradores", "descripcion": "Información de sede", "ciudad": "Barranquilla"},
    "Centro Médico Colmédica Bucaramanga": {"direccion": "Cl 52 A 31 - 68 , Bucaramanga", "coordenadas": [7.115442288584315, -73.11191898409285], "color": "blue", "icono": "hospital", "capacidad": "N° Usuarios/Colaboradores", "descripcion": "Información de sede", "ciudad": "Bucaramanga"},
    "Centro Médico Colmédica Cali": {"direccion": "Cr 40 5C – 118 , Cali", "coordenadas": [3.4222730018219965, -76.543009], "color": "blue", "icono": "hospital", "capacidad": "N° Usuarios/Colaboradores", "descripcion": "Información de sede", "ciudad": "Cali"},
    "Centro Médico Colmédica Las Ramblas": {"direccion": "CC las Ramblas, Kilómetro 10, Cartagena", "coordenadas": [10.519058074115778, -75.46619794203212], "color": "blue", "icono": "hospital", "capacidad": "N° Usuarios/Colaboradores", "descripcion": "Información de sede", "ciudad": "Cartagena"},
    "Centro Médico Colmédica Bocagrande": {"direccion": "Cr 4 # 4 - 78, Cartagena", "coordenadas": [10.398251290207035, -75.55869054232946], "color": "blue", "icono": "hospital", "capacidad": "N° Usuarios/Colaboradores", "descripcion": "Información de sede", "ciudad": "Cartagena"},
    "Centro Médico Colmédica Chía": {"direccion": "Belenus Chía Km 2 vía Chía, Chía", "coordenadas": [4.883582951131957, -74.03724042329465], "color": "blue", "icono": "hospital", "capacidad": "N° Usuarios/Colaboradores", "descripcion": "Información de sede", "ciudad": "Chía"},
    "Centro Médico Colmédica Ibagué": {"direccion": "Cra. 5 # 30 - 05, Ibagué", "coordenadas": [4.443406489429007, -75.22333030682144], "color": "blue", "icono": "hospital", "capacidad": "N° Usuarios/Colaboradores", "descripcion": "Información de sede", "ciudad": "Ibagué"},
    "Centro Médico Colmédica Manizales": {"direccion": "C.C. Sancancio, Cr 27 A 66 - 30, Manizales", "coordenadas": [5.054334221451733, -75.48438483625416], "color": "blue", "icono": "hospital", "capacidad": "N° Usuarios/Colaboradores", "descripcion": "Información de sede", "ciudad": "Manizales"},
    "Centro Médico Colmédica Medellín - El Poblado": {"direccion": "El Poblado, Cr 43B 14 - 44, Medellin", "coordenadas": [6.217569802008974, -75.5599849954142], "color": "blue", "icono": "hospital", "capacidad": "N° Usuarios/Colaboradores", "descripcion": "Información de sede", "ciudad": "Medellín"},
    "Centro Médico Colmédica Neiva": {"direccion": "Cl 19 # 5a - 50, Neiva", "coordenadas": [2.9372380321218237, -75.28714836532676], "color": "blue", "icono": "hospital", "capacidad": "N° Usuarios/Colaboradores", "descripcion":"Información de sede", "ciudad": "Neiva"},
    "Centro Médico Colmédica Pereira": {"direccion": "Megacentro, Cl 19 N 12 – 50, Pereira", "coordenadas": [4.805020850357549, -75.68778748692321], "color": "blue", "icono": "hospital", "capacidad": "N° Usuarios/Colaboradores", "descripcion": "Información de sede", "ciudad": "Pereira"},
    "Centro Médico Colmédica Villavicencio": {"direccion": "Barzal Alto, Cl 32 # 40A – 31, Villavicencio", "coordenadas": [4.1424147251065335, -73.63860592868659], "color": "blue", "icono": "hospital", "capacidad": "N° Usuarios/Colaboradores", "descripcion": "Información de sede", "ciudad": "Villavicencio"},
    "Centro Médico Colmédica Yopal": {"direccion": "Clínica Nieves, Cr 21 35 - 68, Yopal", "coordenadas": [5.327695694529845, -72.38637738635713], "color": "blue", "icono": "hospital", "capacidad": "N° Usuarios/Colaboradores", "descripcion": "Información de", "ciudad": "Yopal"}
}

# --- Inicialización del estado de la sesión para las zonas ---
if 'zonas_emergencia' not in st.session_state:
    st.session_state.zonas_emergencia = []

# --- Lista de Tipos de Evento ---
TIPOS_EVENTO = [
    "Desastre Natural (Sismo, Inundación)",
    "Incendio",
    "Fallo de Servicios Públicos (Agua, Electricidad)",
    "Emergencia de Seguridad (Orden Público)",
    "Pandemia/Emergencia Sanitaria",
    "Falla Tecnológica Mayor",
    "Interrupción de Transporte",
    "Otros"
]

# --- Funciones Auxiliares ---
def remove_accents(input_str):
    """Elimina acentos de los caracteres"""
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])

def crear_mapa_base(location=[4.5709, -74.2973], zoom_start=6, tile_provider="MapLibre"):
    """Crea mapa base optimizado"""
    m = folium.Map(
        location=location,
        zoom_start=zoom_start,
        tiles=TILES[tile_provider]["url"],
        attr=TILES[tile_provider]["attr"],
        control_scale=True,
        prefer_canvas=True
    )
    LocateControl(auto_start=False).add_to(m)
    Fullscreen().add_to(m)
    Draw(
        export=False,
        position="topleft",
        draw_options={
            'polyline': False,
            'rectangle': True,
            'polygon': True,
            'circle': True,
            'marker': False,
            'circlemarker': False
        }
    ).add_to(m)
    return m

def buscar_direccion_colombia(direccion):
    """Geocodificación optimizada"""
    try:
        geolocator = Nominatim(user_agent="continuidad_app", timeout=10)
        location = geolocator.geocode(f"{direccion}, Colombia", exactly_one=True)
        return location if location and "Colombia" in location.address else None
    except Exception:
        return None

def analizar_multiples_zonas(lista_zonas, sedes_fijas):
    """Genera un reporte consolidado, identificando sedes afectadas y sugiriendo alternativas."""
    if not lista_zonas:
        return None

    sedes_afectadas_nombres = set()

    try:
        for zona_dibujada in lista_zonas:
            if 'geometry' not in zona_dibujada:
                continue
            zona_shape = shape(zona_dibujada['geometry'])

            for nombre, datos in sedes_fijas.items():
                punto = Point(datos["coordenadas"][1], datos["coordenadas"][0])
                if zona_shape.contains(punto):
                    sedes_afectadas_nombres.add(nombre)

        sedes_list = []
        for nombre in sedes_afectadas_nombres:
            datos = sedes_fijas[nombre]
            sedes_list.append({
                "Nombre": nombre,
                "Dirección": datos["direccion"],
                "Coordenadas": datos["coordenadas"],
                "Capacidad": datos.get("capacidad", "No especificada"),
                "Descripción Evento": datos.get("descripcion", "N/A"),
                "Ciudad": datos.get("ciudad", "Desconocida")
            })
        df_sedes_afectadas = pd.DataFrame(sedes_list)

        # --- NUEVA LÓGICA PARA ENCONTRAR ALTERNATIVAS ---
        df_alternativas = encontrar_sedes_alternativas(df_sedes_afectadas, sedes_fijas)

        return {
            "total_sedes": len(df_sedes_afectadas),
            "sedes_afectadas": df_sedes_afectadas,
            "sedes_alternativas": df_alternativas, # <-- AÑADIMOS LAS ALTERNATIVAS AL REPORTE
            "zonas": lista_zonas
        }

    except Exception as e:
        st.error(f"Error al generar el reporte multizona: {str(e)}")
        return None

    sedes_afectadas_nombres = set()

    try:
        for zona_dibujada in lista_zonas:
            if 'geometry' not in zona_dibujada:
                continue
            zona_shape = shape(zona_dibujada['geometry'])

            # Evaluar sedes
            for nombre, datos in sedes_fijas.items():
                punto = Point(datos["coordenadas"][1], datos["coordenadas"][0])
                if zona_shape.contains(punto):
                    sedes_afectadas_nombres.add(nombre)

        sedes_list = []
        for nombre in sedes_afectadas_nombres:
            datos = sedes_fijas[nombre]
            sedes_list.append({
                "Nombre": nombre,
                "Dirección": datos["direccion"],
                "Coordenadas": datos["coordenadas"],
                "Capacidad": datos.get("capacidad", "No especificada"),
                "Descripción Evento": datos.get("descripcion", "N/A"),
                "Ciudad": datos.get("ciudad", "Desconocida") # Añadir ciudad al DataFrame
            })
        df_sedes_afectadas = pd.DataFrame(sedes_list)

        return {
            "total_sedes": len(df_sedes_afectadas),
            "sedes_afectadas": df_sedes_afectadas,
            "zonas": lista_zonas
        }

    except Exception as e:
        st.error(f"Error al generar el reporte multizona: {str(e)}")
        return None

def calcular_sedes_cercanas(sede_origen_coords, sedes_fijas, distancia_max_km):
    """Calcula las sedes cercanas a una sede de origen dentro de una distancia máxima."""
    sedes_cercanas_list = []
    
    for nombre, datos in sedes_fijas.items():
        if datos["coordenadas"] == sede_origen_coords: # Evitar la propia sede de origen
            continue
        
        distancia = geodesic(sede_origen_coords, datos["coordenadas"]).km
        if distancia <= distancia_max_km:
            sedes_cercanas_list.append({
                "Nombre Sede": nombre,
                "Dirección": datos["direccion"],
                "Distancia (km)": round(distancia, 2),
                "Capacidad": datos.get("capacidad", "No especificada"),
                "Descripción Evento": datos.get("descripcion", "N/A"),
                "Ciudad": datos.get("ciudad", "Desconocida") # Añadir ciudad
            })
            
    df_sedes_cercanas = pd.DataFrame(sedes_cercanas_list)
    df_sedes_cercanas = df_sedes_cercanas.sort_values(by="Distancia (km)").reset_index(drop=True)
    return df_sedes_cercanas

def generar_graficas_pdf(reporte, sedes_fijas_todas):
    """Genera gráficas optimizadas para PDF relevantes para sedes."""
    figuras = []
    colores_profesionales = ['#4A90E2', '#50E3C2', '#F5A623', '#D0021B', '#BD10E0', '#7ED321', '#9013FE']

    # Gráfica 3: Sedes afectadas vs. Total por Ciudad
    if not reporte["sedes_afectadas"].empty and "Ciudad" in reporte["sedes_afectadas"].columns:
        fig3, ax3 = plt.subplots(figsize=(10, 6))
        
        # Conteo total de sedes por ciudad
        total_sedes_por_ciudad = pd.Series([datos.get("ciudad", "Desconocida") for datos in sedes_fijas_todas.values()]).value_counts()
        
        # Conteo de sedes afectadas por ciudad
        sedes_afectadas_por_ciudad = reporte["sedes_afectadas"]["Ciudad"].value_counts()

        # Combinar para obtener los datos que queremos graficar
        # Usamos `reindex` para asegurar que todas las ciudades estén presentes
        # y `fillna(0)` para las ciudades que no tienen sedes afectadas
        df_comparacion = pd.DataFrame({
            'Total Sedes': total_sedes_por_ciudad,
            'Sedes Afectadas': sedes_afectadas_por_ciudad
        }).fillna(0)
        
        df_comparacion.sort_values(by='Total Sedes', ascending=False).plot(
            kind='bar', ax=ax3, color=['#4A90E2', '#D0021B']
        )
        
        ax3.set_title('Sedes Afectadas vs. Total de Sedes por Ciudad', fontsize=14, weight='bold')
        ax3.set_xlabel('Ciudad', fontsize=12)
        ax3.set_ylabel('Número de Sedes', fontsize=12)
        ax3.tick_params(axis='x', rotation=45, labelsize=10)
        plt.setp(ax3.get_xticklabels(), ha="right", rotation_mode="anchor") # Asegurar alineación
        ax3.spines['top'].set_visible(False)
        ax3.spines['right'].set_visible(False)
        ax3.grid(axis='y', linestyle='--', alpha=0.7)
        ax3.yaxis.set_major_locator(plt.MaxNLocator(integer=True))
        ax3.set_ylim(bottom=0)
        plt.tight_layout()
        figuras.append(fig3)

    return figuras

def crear_pdf(reporte, tipo_evento, descripcion_emergencia="", sedes_fijas_todas=SEDES_FIJAS):
    """Crea un PDF con el reporte de emergencia de sedes."""
    try:
        pdf = FPDF()
        pdf.add_page()

        try:
            # Obtener el directorio del script actual
            current_script_dir = os.path.dirname(__file__)
            logo_path = os.path.join(current_script_dir, 'assets', 'logo_colmedica.png')
            pdf.image(logo_path, x=10, y=8, w=40)
        except FileNotFoundError:
            st.warning("Advertencia: No se encontró el archivo del logo para el PDF.")

        pdf.set_font("Arial", size=12)

        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, txt="REPORTE DE EMERGENCIA", ln=1, align='C')
        pdf.set_font("Arial", size=12)
        # Obtener la hora actual en la zona horaria de Bogotá
        bogota_tz = pytz.timezone('America/Bogota')
        fecha_actual = datetime.now(bogota_tz)
        pdf.cell(0, 10, txt=f"Fecha: {fecha_actual.strftime('%Y-%m-%d %H:%M')}", ln=1)
        pdf.ln(10)

        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, txt="Información del Evento", ln=1)
        pdf.set_font("Arial", size=12)
        pdf.cell(0, 8, txt=f"Tipo de evento: {remove_accents(tipo_evento)}", ln=1)
        descripcion_simple = remove_accents(descripcion_emergencia)
        pdf.multi_cell(0, 8, txt=f"Descripción: {descripcion_simple}")
        pdf.ln(10)

        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, txt="Resumen de la Emergencia", ln=1)
        pdf.set_font("Arial", size=12)
        pdf.cell(0, 8, txt=f"Total sedes afectadas: {reporte['total_sedes']}", ln=1)
        
        pdf.ln(10)

        # --- Gráficas ---
        figuras_pdf = generar_graficas_pdf(reporte, sedes_fijas_todas) 
        temp_files = []
        try:
            for fig in figuras_pdf:
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmpfile:
                    fig.savefig(tmpfile.name, dpi=150, bbox_inches='tight')
                    temp_files.append(tmpfile.name)
                plt.close(fig)

            for temp_file in temp_files:
                pdf.add_page()
                pdf.image(temp_file, x=10, w=190)
        finally:
            for temp_file in temp_files:
                try:
                    os.unlink(temp_file)
                except:
                    pass

        # --- Tabla de Sedes Afectadas ---
        if not reporte["sedes_afectadas"].empty:
            pdf.add_page()
            pdf.set_font("Arial", 'B', 14)
            pdf.cell(0, 10, txt="Sedes Afectadas", ln=1)
            pdf.set_font("Arial", 'B', 9)
            
            col_width_nombre = 40
            col_width_direccion = 60
            col_width_capacidad = 30
            col_width_evento = 30
            col_width_ciudad = 30
            
            pdf.set_fill_color(200, 220, 255)
            pdf.cell(col_width_nombre, 8, "Nombre Sede", 1, 0, 'C', True)
            pdf.cell(col_width_direccion, 8, "Dirección", 1, 0, 'C', True)
            pdf.cell(col_width_capacidad, 8, "Capacidad", 1, 0, 'C', True)
            pdf.cell(col_width_evento, 8, "Descripción", 1, 0, 'C', True)
            pdf.cell(col_width_ciudad, 8, "Ciudad", 1, 1, 'C', True)
            
            pdf.set_font("Arial", size=8)
            pdf.set_fill_color(255, 255, 255)
            for _, row in reporte["sedes_afectadas"].iterrows():
                nombre_simple = remove_accents(row['Nombre'])[:25]
                direccion_simple = remove_accents(row['Dirección'])[:35]
                # Convertir a string para evitar errores si es None o NaN
                capacidad_simple = remove_accents(str(row.get('Capacidad', '')))[:20]
                evento_simple = remove_accents(row['Descripción Evento'])[:20]
                ciudad_simple = remove_accents(row['Ciudad'])[:20]

                pdf.cell(col_width_nombre, 8, txt=nombre_simple, border=1, align='L')
                pdf.cell(col_width_direccion, 8, txt=direccion_simple, border=1, align='L')
                pdf.cell(col_width_capacidad, 8, txt=capacidad_simple, border=1, align='L')
                pdf.cell(col_width_evento, 8, txt=evento_simple, border=1, align='L')
                pdf.cell(col_width_ciudad, 8, txt=ciudad_simple, border=1, align='L', ln=1)

        # --- Tabla de Sedes Alternativas Sugeridas ---
        if 'sedes_alternativas' in reporte and not reporte['sedes_alternativas'].empty:
            pdf.add_page()
            pdf.set_font("Arial", 'B', 14)
            pdf.cell(0, 10, txt="4. Sedes Alternativas Sugeridas", ln=1)
            pdf.set_font("Arial", 'B', 9)
            
            # Definir anchos de columna para la nueva tabla
            col_alt = 55
            col_cercana = 55
            col_ciudad_alt = 40
            col_dist = 30
            
            # Cabecera de la tabla
            pdf.set_fill_color(200, 220, 255) # Un gris claro para diferenciar
            pdf.cell(col_cercana, 8, "Sede Afectada", 1, 0, 'C', True)
            pdf.cell(col_alt, 8, "Sede Alternativa", 1, 0, 'C', True)
            pdf.cell(col_ciudad_alt, 8, "Ciudad", 1, 0, 'C', True)
            pdf.cell(col_dist, 8, "Distancia (km)", 1, 1, 'C', True)
            
            # Contenido de la tabla
            pdf.set_font("Arial", size=8)
            pdf.set_fill_color(255, 255, 255)
            for _, row in reporte['sedes_alternativas'].iterrows():
                alternativa = remove_accents(row['Sede Alternativa'])[:35]
                cercana_a = remove_accents(row['Cercana a (Sede Afectada)'])[:35]
                ciudad = remove_accents(row['Ciudad'])[:25]
                distancia = str(row['Distancia (km)'])
                
                pdf.cell(col_cercana, 8, txt=cercana_a, border=1, align='L')
                pdf.cell(col_alt, 8, txt=alternativa, border=1, align='L')
                pdf.cell(col_ciudad_alt, 8, txt=ciudad, border=1, align='L')
                pdf.cell(col_dist, 8, txt=distancia, border=1, align='C', ln=1)
        # --- FIN DEL NUEVO CÓDIGO ---

        # Este bloque final se encarga de guardar el PDF en memoria
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_pdf:
            pdf.output(tmp_pdf.name)
            tmp_pdf.seek(0)
            pdf_bytes = tmp_pdf.read()

        try:
            os.unlink(tmp_pdf.name)
        except Exception as e:
            st.warning(f"No se pudo eliminar el archivo PDF temporal: {e}")

        return pdf_bytes

    except Exception as e:
        st.error(f"Error al generar el PDF: {str(e)}")
        return None

def generar_excel_reporte(reporte, tipo_evento, descripcion):
    """Genera un archivo Excel con el reporte de sedes afectadas."""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        bogota_tz = pytz.timezone('America/Bogota')
        fecha_actual_str = datetime.now(bogota_tz).strftime('%Y-%m-%d %H:%M')
        resumen_data = {
            "Parámetro": ["Tipo de Evento", "Descripción", "Fecha del Reporte", "Total Sedes Afectadas"],
            "Valor": [tipo_evento, descripcion, fecha_actual_str, reporte['total_sedes']]
        }
        pd.DataFrame(resumen_data).to_excel(writer, sheet_name='Resumen', index=False)
        
        if not reporte["sedes_afectadas"].empty:
            # Selecciona solo las columnas que quieres exportar al Excel para 'Sedes Afectadas'
            df_export = reporte["sedes_afectadas"][["Nombre", "Dirección", "Capacidad", "Descripción Evento", "Ciudad"]] # Añadida Ciudad
            df_export.to_excel(writer, sheet_name='Sedes Afectadas', index=False)
    
    output.seek(0)
    return output.getvalue()

def encontrar_sedes_alternativas(df_sedes_afectadas, sedes_fijas_todas, num_alternativas=3, distancia_max_km=15):
    """
    Para cada sede afectada, encuentra las 'num_alternativas' sedes no afectadas más cercanas.
    """
    if df_sedes_afectadas.empty:
        return pd.DataFrame()

    nombres_afectadas = set(df_sedes_afectadas['Nombre'])
    sedes_no_afectadas = {nombre: datos for nombre, datos in sedes_fijas_todas.items() if nombre not in nombres_afectadas}
    
    lista_alternativas_final = []

    for _, sede_afectada in df_sedes_afectadas.iterrows():
        nombre_origen = sede_afectada['Nombre']
        coords_origen = sede_afectada['Coordenadas']
        
        candidatas = []
        for nombre_alternativa, datos_alternativa in sedes_no_afectadas.items():
            distancia = geodesic(coords_origen, datos_alternativa["coordenadas"]).km
            if distancia <= distancia_max_km:
                candidatas.append({
                    "Sede Alternativa": nombre_alternativa,
                    "Cercana a (Sede Afectada)": nombre_origen,
                    "Ciudad": datos_alternativa.get("ciudad", "Desconocida"),
                    "Distancia (km)": round(distancia, 2)
                })
        
        candidatas_ordenadas = sorted(candidatas, key=lambda x: x['Distancia (km)'])
        lista_alternativas_final.extend(candidatas_ordenadas[:num_alternativas])

    return pd.DataFrame(lista_alternativas_final)



def get_table_download_link(df, filename="reporte.csv"):
    """Genera un enlace para descargar un dataframe como CSV"""
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">Descargar archivo CSV</a>'
    return href

# --- INTERFAZ DE STREAMLIT ---
with st.sidebar:
    try:
        # Usar la ruta absoluta del logo para mayor robustez
        current_script_dir = os.path.dirname(__file__)
        logo_path = os.path.join(current_script_dir, 'assets', 'logo_colmedica.png')
        st.image(logo_path, use_container_width=True)
    except FileNotFoundError:
        st.sidebar.title("Sistema de Continuidad")
        st.sidebar.warning("No se encontró el archivo 'assets/logo_colmedica.png'. Asegúrate de que la carpeta 'assets' y el logo existan en el mismo directorio que tu script.")


    st.header("⚙️ Configuración")
    tile_provider = st.selectbox("Seleccionar tipo de mapa", list(TILES.keys()), index=0)

    st.header("📍 Zonas de Emergencia por Dirección")
    with st.expander("BUSCAR DIRECCIÓN EN COLOMBIA", expanded=True):
        direccion = st.text_input(label="Buscar dirección para emergencia:", placeholder="Ej: Calle 100 #15-50, Bogotá", key="direccion_emergencia_input")

        if st.button("🗺️ Encontrar en el mapa y crear zona"):
            if direccion:
                with st.spinner("Buscando..."):
                    location = buscar_direccion_colombia(direccion)
                    if location:
                        st.session_state.emergencia_location = {"coords": [location.latitude, location.longitude], "address": location.address}
                        punto_emergencia = Point(st.session_state.emergencia_location['coords'][1], st.session_state.emergencia_location['coords'][0])
                        # Crea un círculo con un radio de ~500 metros (0.005 grados)
                        zona_circular = punto_emergencia.buffer(0.005)
                        zona_para_anadir = {'geometry': mapping(zona_circular)}
                        st.session_state.zonas_emergencia.append(zona_para_anadir)
                        st.success(f"✅ Ubicación encontrada y zona circular añadida para: {location.address}!")
                        st.rerun() # Rerun para actualizar el mapa con la nueva zona
                    else:
                        st.error("Dirección no encontrada")

    # Sección para calcular sedes cercanas a una sede fija
    st.header("🗺️ Sedes Cercanas")
    sede_seleccionada = st.selectbox("Seleccione una sede para buscar cercanas:", [""] + list(SEDES_FIJAS.keys()))
    distancia_km = st.slider("Distancia máxima (km) para buscar sedes cercanas:", 1, 100, 10)

# --- MAPA Y LÓGICA PRINCIPAL ---
# Asegúrate de que 'm' se define aquí, antes de cualquier uso
m = crear_mapa_base(tile_provider=tile_provider)

# Mostrar sedes fijas con popups mejorados
for nombre, datos in SEDES_FIJAS.items():
    popup_html = f"""
    <b>{nombre}</b><br>
    Dirección: {datos['direccion']}<br>
    Ciudad: {datos.get('ciudad', 'Desconocida')}<br>
    Capacidad: {datos.get('capacidad', 'No especificada')}<br>
    Descripción: {datos.get('descripcion', 'N/A')}
    """
    folium.Marker(
        location=datos["coordenadas"],
        popup=folium.Popup(popup_html, max_width=300),
        icon=folium.Icon(color=datos["color"], icon=datos["icono"], prefix='fa')
    ).add_to(m)

# Marcar sedes cercanas en el mapa si se ha seleccionado una sede de origen
if sede_seleccionada:
    coords_sede_origen = SEDES_FIJAS[sede_seleccionada]["coordenadas"]
    df_cercanas = calcular_sedes_cercanas(coords_sede_origen, SEDES_FIJAS, distancia_km)
    
    if not df_cercanas.empty:
        for _, row in df_cercanas.iterrows():
            nombre_sede = row["Nombre Sede"]
            if nombre_sede in SEDES_FIJAS:
                coords = SEDES_FIJAS[nombre_sede]["coordenadas"]
                
                popup_html_cercanas = f"""
                <b>{nombre_sede}</b><br>
                <strong style='color:green;'>Distancia: {row['Distancia (km)']} km</strong><br>
                Dirección: {row['Dirección']}<br>
                Ciudad: {row['Ciudad']}<br>
                Capacidad: {row['Capacidad']}<br>
                Descripción: {row['Descripción Evento']}
                """
                
                folium.Marker(
                    location=coords,
                    popup=folium.Popup(popup_html_cercanas, max_width=300), # Usamos el nuevo HTML
                    icon=folium.Icon(color='green', icon='hospital', prefix='fa')
                ).add_to(m)
                
# Visualizar las zonas ya guardadas
if st.session_state.zonas_emergencia:
    for i, zona in enumerate(st.session_state.zonas_emergencia):
        folium.GeoJson(
            zona['geometry'],
            style_function=lambda x: {'fillColor': 'red', 'color': 'black', 'weight': 2.5, 'fillOpacity': 0.4},
            tooltip=f"Zona de Emergencia #{i+1}"
        ).add_to(m)

# Centrar mapa en la última ubicación buscada (si aplica)
if 'emergencia_location' in st.session_state:
    m.location = st.session_state.emergencia_location["coords"]
    m.zoom_start = 15

# Mostrar mapa
map_data = st_folium(m, width=1200, height=600, key="mapa_principal")

# --- Sección para gestionar y analizar las zonas ---
st.header("Gestión de Zonas de Emergencia Dibujadas")
col1, col2, col3 = st.columns([2, 2, 1])

with col1:
    # Guardar el último dibujo en el estado de la sesión para que persista
    if map_data.get("last_active_drawing"):
        st.session_state.last_drawn = map_data["last_active_drawing"]

    if 'last_drawn' in st.session_state and st.session_state.last_drawn:
        st.info("Se ha detectado una nueva zona dibujada en el mapa.")
        if st.button("➕ Añadir Zona Dibujada para análisis", use_container_width=True):
            st.session_state.zonas_emergencia.append(st.session_state.last_drawn)
            del st.session_state.last_drawn  # Limpiar el dibujo temporal
            st.success("¡Zona añadida! Puedes dibujar otra o analizar las zonas marcadas.")
            st.rerun()

with col2:
    if st.session_state.zonas_emergencia:
        num_zonas = len(st.session_state.zonas_emergencia)
        st.markdown(f"**Tiene {num_zonas} zona(s) de emergencia marcada(s) en el mapa.**")
        
        # Usar st.selectbox para Tipo de Evento
        tipo_evento = st.selectbox("Tipo de Evento (para reporte):", TIPOS_EVENTO, key="tipo_evento_select")
        descripcion_emergencia = st.text_area("Descripción del Evento (para reporte):", "Descripción detallada del incidente y su impacto en las sedes.", key="desc_evento_input")

        if st.button("🔬 Analizar Zonas Marcadas y Generar Reporte", type="primary", use_container_width=True):
            with st.spinner("Analizando todas las zonas y generando reporte..."):
                reporte = analizar_multiples_zonas(st.session_state.zonas_emergencia, SEDES_FIJAS)
                if reporte:
                    st.session_state.ultimo_reporte = reporte
                    st.session_state.ultimo_tipo_evento = tipo_evento
                    st.session_state.ultima_descripcion = descripcion_emergencia
                    st.success("Reporte generado con éxito.")
                    st.rerun() # Rerun para mostrar los resultados en la interfaz

with col3:
    if st.session_state.zonas_emergencia:
        if st.button("🗑️ Limpiar Todas las Zonas", use_container_width=True):
            st.session_state.zonas_emergencia = []
            if 'last_drawn' in st.session_state:
                del st.session_state.last_drawn
            # También limpiar los datos del último reporte si existen
            if 'ultimo_reporte' in st.session_state:
                del st.session_state.ultimo_reporte
            if 'ultimo_tipo_evento' in st.session_state:
                del st.session_state.ultimo_tipo_evento
            if 'ultima_descripcion' in st.session_state:
                del st.session_state.ultima_descripcion
            st.info("Todas las zonas de emergencia y el reporte anterior han sido eliminados.")
            st.rerun()

# --- Mostrar Resultados del Reporte ---
if 'ultimo_reporte' in st.session_state and st.session_state.ultimo_reporte:
    st.markdown("---")
    st.header("Resultados del Análisis de Zonas de Emergencia")

    reporte_final = st.session_state.ultimo_reporte

    st.subheader(f"Total de Sedes Afectadas: {reporte_final['total_sedes']}")

    if not reporte_final["sedes_afectadas"].empty:
        st.write("### 🏢 Sedes Afectadas")
        
        # --- AJUSTE REALIZADO AQUÍ ---
        # Creamos una copia del DataFrame pero sin la columna 'Coordenadas' para mostrarla en la app
        df_vista = reporte_final["sedes_afectadas"].drop(columns=['Coordenadas'])
        st.dataframe(df_vista)
        
        # El botón de descarga seguirá exportando el DataFrame original con todas las columnas
        st.markdown(get_table_download_link(reporte_final["sedes_afectadas"], "sedes_afectadas.csv"), unsafe_allow_html=True)
    else:
        st.info("No se encontraron sedes afectadas dentro de las zonas marcadas.")

    # Mostrar sedes cercanas calculadas previamente
    if sede_seleccionada and 'df_cercanas' in locals() and not df_cercanas.empty: # Check if df_cercanas exists from sidebar logic
        st.markdown("---")
        st.subheader(f"Sedes Cercanas a {sede_seleccionada}")
        st.dataframe(df_cercanas)
        st.markdown(get_table_download_link(df_cercanas, f"sedes_cercanas_{sede_seleccionada}.csv"), unsafe_allow_html=True)

    # Generación de PDF y Excel
    st.markdown("---")
    st.subheader("Generar Reportes")
    col_pdf, col_excel = st.columns(2)

    with col_pdf:
        # Pasar SEDES_FIJAS a crear_pdf
        pdf_bytes = crear_pdf(
            reporte_final,
            st.session_state.ultimo_tipo_evento,
            st.session_state.ultima_descripcion,
            SEDES_FIJAS # Pasar el diccionario completo de sedes
        )
        if pdf_bytes:
            st.download_button(
                label="Descargar Reporte PDF",
                data=pdf_bytes,
                file_name=f"Reporte_Emergencia_Sedes_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                mime="application/pdf",
                use_container_width=True
            )

    with col_excel:
        excel_bytes = generar_excel_reporte(
            reporte_final,
            st.session_state.ultimo_tipo_evento,
            st.session_state.ultima_descripcion
        )
        if excel_bytes:
            st.download_button(
                label="Descargar Reporte Excel",
                data=excel_bytes,
                file_name=f"Reporte_Emergencia_Sedes_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

    st.markdown("---")
    st.subheader("Gráficas del Reporte")
    
    # Gráficas para sedes afectadas
    if not reporte_final["sedes_afectadas"].empty:


        # NUEVA GRÁFICA: Sedes Afectadas vs. Total por Ciudad
        if "Ciudad" in reporte_final["sedes_afectadas"].columns:
            st.write("#### Sedes Afectadas vs. Total de Sedes por Ciudad")
            fig_ciudad, ax_ciudad = plt.subplots(figsize=(10, 6))
            
            # Conteo total de sedes por ciudad del diccionario original SEDES_FIJAS
            total_sedes_por_ciudad = pd.Series([datos.get("ciudad", "Desconocida") for datos in SEDES_FIJAS.values()]).value_counts()
            
            # Conteo de sedes afectadas por ciudad (del DataFrame de reporte)
            sedes_afectadas_por_ciudad = reporte_final["sedes_afectadas"]["Ciudad"].value_counts()

            # Combinar y preparar DataFrame para la gráfica
            df_comparacion = pd.DataFrame({
                'Total Sedes': total_sedes_por_ciudad,
                'Sedes Afectadas': sedes_afectadas_por_ciudad
            }).fillna(0) # Rellenar con 0 donde no hay sedes afectadas

            df_comparacion.sort_values(by='Total Sedes', ascending=False).plot(
                kind='bar', ax=ax_ciudad, color=['#4A90E2', '#D0021B']
            )
            
            ax_ciudad.set_title('Comparación de Sedes Afectadas y Totales por Ciudad')
            ax_ciudad.set_xlabel('Ciudad')
            ax_ciudad.set_ylabel('Número de Sedes')
            ax_ciudad.tick_params(axis='x', rotation=45)
            plt.setp(ax_ciudad.get_xticklabels(), ha="right", rotation_mode="anchor")
            ax_ciudad.yaxis.set_major_locator(plt.MaxNLocator(integer=True))
            ax_ciudad.set_ylim(bottom=0)
            st.pyplot(fig_ciudad)
            plt.close(fig_ciudad)
    else:
        st.info("No hay datos de sedes afectadas para generar gráficas.")
