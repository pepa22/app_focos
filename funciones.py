import pandas as pd
import geopandas as gpd
from shapely.geometry import Polygon
import zipfile
import os
import numpy as np
from pathlib import Path
import re
import shutil
import locale
from datetime import datetime
import json

import plotly.graph_objs as go
from plotly.offline import plot
from plotly.subplots import make_subplots



# Lee la configuración desde el archivo JSON
with open('config.json') as config_file:
    config = json.load(config_file)
    
BASE_DIR = config["BASE_DIR"]
RESULTS_FOLDER_FOCOS = os.path.join(BASE_DIR, config["RESULTS_FOLDER_FOCOS"])
path_logo = "https://catalogos4.conae.gov.ar/recursosCatalogos/imagenes/conaeLogoTransp.png"

def carpeta_vacia(ruta):
    carpeta = Path(ruta)
    return not any(carpeta.iterdir())

def crear_carpeta(folder):
    Path(folder).mkdir(parents=True, exist_ok=True)

def eliminar_carpeta(folder):
    shutil.rmtree(folder, ignore_errors=True)
       
def leer_csv(files):
    return pd.concat([pd.read_csv(file) for file in files])

def procesar_tablas(df):
    df['Desde'] = pd.to_datetime(df['Desde'])
    df['Hasta'] = pd.to_datetime(df['Hasta'])
    df['periodo'] = (df['Hasta'] - df['Desde']).astype(str)
    # se vuelve a pasar a string porque el proceso de generacion de shape no permite datos tipo datetime
    df['Desde'] = df['Desde'].astype(str)
    df['Hasta'] = df['Hasta'].astype(str)
    return df

def crear_zip(result_folder, zip_filepath):
    with zipfile.ZipFile(zip_filepath, 'w') as zip_result:
        for root, dirs, files in os.walk(result_folder):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, result_folder)
                zip_result.write(file_path, arcname=arcname)
    
#------------------------------------------------------------------------------------------
# funcion para estandarizar y analizar las tablas de depatamentos/provincia
def departamentos_mes_pivoTable(data):
        #print(data[:3])
       # data.sort_values(by='Mes')
        data['Mes'] = pd.to_datetime(data['Mes']).dt.strftime('%Y-%m')      
        
        totalFocos = data['Cantidad'].sum()
        print('total de focos: ', totalFocos)
        # lista de nombres de los departamentos
        lista_deptos = data.loc[:, ['Provincia','Departamento', 'in1']].drop_duplicates(subset=['in1'])
        #print(lista_deptos[:4])
        # agrupamiento de los focos segun el mes y la localidad, donde Cantidad es la suma de los focos totales
        df_pivot = data.pivot_table(index='in1', columns='Mes', values='Cantidad', aggfunc='sum', fill_value=0).reset_index()
        
        #print(df_sum[:4])
        #print(lista_deptos)
       # lo mergeo con el listado de nombres de departamentos porque se habia pedido al hacer el group
        merged_data_depto = df_pivot.merge(lista_deptos, on='in1', how='inner')
        #print(merged_data_depto[:14])
        
        #verifico que los focos sean los mismos al final del proceso
        suma_columna = df_pivot['in1'].sum() #(saco esta columna en la sumatoria total de valores de la tabla)
        totalFocos_fin = df_pivot.sum().sum()
        total = totalFocos_fin -suma_columna
        print('total de focos al final: ', total)
        #print(df_simplificado[:5])
                
        return merged_data_depto

def departamentos_mes(data):
       # print(data[:3])
       # data.sort_values(by='Mes')
        data['Mes'] = pd.to_datetime(data['Mes'])     
        
        totalFocos = data['Cantidad'].sum()
        print('total de focos: ', totalFocos)
        # lista de nombres de los departamentos
        lista_deptos = data.loc[:, ['Provincia','Departamento', 'in1']].drop_duplicates(subset=['in1'])
        #print(lista_deptos[:4])
        # agrupamiento de los focos segun el mes y la localidad, donde Cantidad es la suma de los focos totales
        df_sum = data.groupby(['in1', data['Mes'].dt.strftime('%Y-%m')])['Cantidad'].sum().reset_index()
        totalFocos_dfsum = df_sum['Cantidad'].sum()
        print('total de focos al suma: ', totalFocos_dfsum)  
        #print(df_sum[:4])
        # Extraer año y mes 
        df_sum['Mes'] = pd.to_datetime(df_sum['Mes'])
        df_sum['Año'] = df_sum['Mes'].dt.year
        df_sum['Mes_Num'] = df_sum['Mes'].dt.month
        df_sum['Año']  = df_sum['Año'].astype(str) 
        #df_sum['Mes_Num'] = df_sum['Mes_Num'].astype(str) 
        
        meses_ordenados = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
        #df_sum['Meses'] = pd.Categorical(df_sum['Mes_Num'].map(dict(zip(range(1, 13), meses_ordenados))), categories=meses_ordenados)
        df_sum['Meses'] = pd.Categorical(df_sum['Mes_Num'].apply(lambda x: meses_ordenados[x-1]), categories=meses_ordenados)
        #df_sum['Mes'] = df_sum['Mes'].dt.strftime('%m-%Y')
        df_sum['Meses'] = df_sum['Meses'].astype(str) 
        #print(df_sum[:4])
        #print(lista_deptos)
       # lo mergeo con el listado de nombres de departamentos porque se habia pedido al hacer el group
        merged_data_depto = df_sum.merge(lista_deptos, on='in1', how='inner')
        #print(merged_data_depto[:14])
        
        totalFocos_fin = merged_data_depto['Cantidad'].sum()
        print('total de focos al final: ', totalFocos_fin)
        #print(df_simplificado[:5])
                
        return merged_data_depto
    
def departamentos_periodo(data):
        data = procesar_tablas(data)
        totalFocos = data['Cantidad'].sum()
        print('total de focos: ', totalFocos)
        data['total_focos'] = data.groupby(['in1'])['Cantidad'].transform('sum')
        print(data[:5])
        df_simplificado = data.drop_duplicates(subset=['in1'])
        totalFocosFin = df_simplificado['total_focos'].sum()
        print('total de focos procesados: ', totalFocosFin)
              
        return df_simplificado

def provincia_mes_pivoTable(data):
    
    data['Mes'] = pd.to_datetime(data['Mes']).dt.strftime('%Y-%m') 
    totalFocos = data['Cantidad'].sum()
    print('total de focos: ', totalFocos)
   # lista_prov = data.loc[:, ['Provincia']]
   # df_sum = data.groupby(['Provincia', data['Mes'].dt.strftime('%Y-%m')])['Cantidad'].sum().reset_index()
    df_pivot = data.pivot_table(index='Provincia', columns='Mes', values='Cantidad', aggfunc='sum', fill_value=0).reset_index()
   
    #suma_columna = df_pivot['Mes'].sum() #(saco esta columna en la sumatoria total de valores de la tabla)
    # totalFocos_fin = df_pivot.sum().
    # total = totalFocos_fin
    # print('total de focos al final: ', total)
    
    return df_pivot   
   
def provincia_mes(data):
    
    data['Mes'] = pd.to_datetime(data['Mes'])
    totalFocos = data['Cantidad'].sum()
    print('total de focos: ', totalFocos)
   # lista_prov = data.loc[:, ['Provincia']]
    df_sum = data.groupby(['Provincia', data['Mes'].dt.strftime('%Y-%m')])['Cantidad'].sum().reset_index()
     # Extraer año y mes 
    df_sum['Mes'] = pd.to_datetime(df_sum['Mes'])
    df_sum['Año'] = df_sum['Mes'].dt.year
    df_sum['Mes_Num'] = df_sum['Mes'].dt.month
    df_sum['Año']  = df_sum['Año'].astype(str) 
    #df_sum['Mes_Num'] = df_sum['Mes_Num'].astype(str) 
    
    # Ordenar los meses de forma natural
    meses_ordenados = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
   # df_sum['Meses'] = pd.Categorical(df_sum['Mes_Num'].map(dict(zip(range(1, 13), meses_ordenados))), categories=meses_ordenados)
    df_sum['Meses'] = pd.Categorical(df_sum['Mes_Num'].apply(lambda x: meses_ordenados[x-1]), categories=meses_ordenados)
    df_sum['Mes'] = df_sum['Mes'].dt.strftime('%m-%Y')
    df_sum['Meses'] = df_sum['Meses'].astype(str) 
    #print(df_sum[:5])
    totalFocos_fin = df_sum['Cantidad'].sum()
    print('total de focos procesadosa: ', totalFocos_fin)
    return df_sum
     # lo mergeo con el listado de nombres de departamentos porque se habia pedido al hacer el group
   # merged_data_prov = df_sum.merge(lista_prov, on='Provincia', how='inner')
    
def provincia_periodo(data):
    data = procesar_tablas(data)
    totalFocos = data['Cantidad'].sum()
    print('total de focos: ', totalFocos)
    data['total_focos'] = data.groupby('Provincia')['Cantidad'].transform('sum')
    ''' #------------------------------------------------------------------------------
        # Para verificar si el agrupamiento es ok 
        # Filtrar los registros donde la provincia sea "Chaco"
        # chaco_data = data[data['Provincia'] == 'Chaco']
        # Visualizar los registros filtrados en la terminal
        # print(chaco_data)
        #-------------------------------------------------------------------------'''
    df_simplificado = data.drop_duplicates(subset='Provincia')
    totalFocosFin = df_simplificado['total_focos'].sum()
    print('total de focos procesados: ', totalFocosFin)
    
    return df_simplificado


def sinAgrupar_periodo(data):
    data = procesar_tablas(data)
    data['total_focos'] = data['Cantidad'].sum()
    totalFocos = data['Cantidad'].sum()
    print('total de focos: ', totalFocos)
    #print(data[:8])
    # # Crear tabla pivote con una columna por cada satélite y su valor en la columna "Cantidad"
    
    f_total = data.pivot_table(index=['total_focos', 'periodo', 'Desde', 'Hasta'], columns='Satélite', values='Cantidad', aggfunc='sum').reset_index()
    totalFocosFin = f_total['total_focos'].sum()
    print('total de focos procesados: ', totalFocosFin)
   
    #print(f_total)
    return f_total

def sinAgrupar_mes(data):
    totalFocos = data['Cantidad'].sum()
    print('total de focos: ', totalFocos)
    data['Mes'] = pd.to_datetime(data['Mes'])
    #print(data[:5])   
    df_sum = data.groupby([data['Mes'].dt.strftime('%Y-%m')])['Cantidad'].sum().reset_index()
    df_sum['Mes'] = pd.to_datetime(df_sum['Mes'])
    df_sum['Año'] = df_sum['Mes'].dt.year
    df_sum['Mes_Num'] = df_sum['Mes'].dt.month
    #print(df_sum[:5])
    # Ordenar los meses de forma natural
    meses_ordenados = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
    
    df_sum['Meses'] = pd.Categorical(df_sum['Mes_Num'].apply(lambda x: meses_ordenados[x-1]), categories=meses_ordenados)
   # print(df_sum[:5])
    df_sum['Año']  = df_sum['Año'].astype(str) 
    df_sum['Mes_Num'] = df_sum['Mes_Num'].astype(str) 
    df_sum['Mes'] = df_sum['Mes'].dt.strftime('%m-%Y')
    df_sum['Meses'] = df_sum['Meses'].astype(str) 
    
    #print('tabla de salida del procesamiento: ',df_sum[:10])
    
    totalFocos_fin = df_sum['Cantidad'].sum()
    print('total de focos procesados: ', totalFocos_fin)
    
    return(df_sum)


def normalizar_datos(datos):
    # Normalizar los datos para que estén en el rango de 0 a 1
    if len(datos) > 1:
        min_val = np.min(datos)
        max_val = np.max(datos)
        # Verificar si hay división por cero
        if max_val - min_val != 0:
                return (datos - min_val) / (max_val - min_val)
        else:
                return datos  # Si la diferencia es cero, devolver los mismos datos sin normalizar
    else:
        return datos  # Si hay pocos datos, devolver los mismos datos

 
# ---------------------------------------------------------------------------------------------------------------
# ----------generacion de los shape de salida-------------------------------------------------------
def shape_focos_depto(data, dept, path, conf):
    # hago una copia de los datos del shape original para luego obtener las coordenadas de vertices de los poligonos
    depto = dept.copy()
    depto['in1'] = depto['in1'].astype(int)
       
    #print(data)
    if 'Mes' in data.columns:
        
        data = departamentos_mes_pivoTable(data)
        #print(data[:3])
        # hago el merge de la tabla con los datos del shape base de departamentos
        merged_data_depto = data.merge(depto, on='in1', how='inner')
        #print(merged_data_depto[:3])
        
        # limpio la tabla
        # borro las columnas duplicadas o que no brindan informacion
        borrar =['objeto','fdc', 'gna', 'gid', 'sag', 'in1','nam']
        merged_data_dept_simp = merged_data_depto.drop(borrar, axis=1)
        #print(merged_data_dept_simp[:5])
       
        
    else:
        #se procesan los datos de los focos del periodo
        data = departamentos_periodo(data)
        # hago el merge de la tabla con los datos del shape base de departamentos
        merged_data_depto = pd.merge(data, depto, left_on='in1', right_on='in1', how='inner')
        # borro las columnas duplicadas o que no brindan informacion
        borrar =['Satélite', 'Instrumento','Cantidad','gid','objeto','sag','gna', 'nam','fdc']
        merged_data_dept_simp = merged_data_depto.drop(borrar, axis=1)
        # funciones para generar los graficos en html1
        grafico_barra_total_depto(merged_data_dept_simp, path, conf)
        
    # genero dataframe de geopandas para exportar como shape
    merged_data_depto_geo = gpd.GeoDataFrame(merged_data_dept_simp, geometry=merged_data_depto['geometry'])
   
    return merged_data_depto_geo

def shape_focos_prov(data, prov, path, conf):
   # verifico que tipo de datos tiene el dataframe de focos    
    if 'Mes' in data.columns:
        data = provincia_mes_pivoTable(data)   
        merged_data_prov = data.merge(prov, left_on='Provincia', right_on='nam', how='left')
        columns_to_drop = ['nam', 'entidad', 'fdc', 'gna', 'gid', 'sag', 'in1']
        merged_data_prov_simpl = merged_data_prov.drop(columns_to_drop, axis=1)
        
       # graficos
        # grafico_barra_mes_prov(data, path, conf)
        # grafico_lineas_mes_prov(data, path, conf)
        #grafico_heatmap_mes_prov_ind(data, path)
        
    else:
        # se procesan los datos de los focos del periodo
        data = provincia_periodo(data)
        # hago el merge de la tabla con los datos del shape base de departamentos
        merged_data_prov = pd.merge(data, prov, left_on='Provincia', right_on='nam', how='left')
        # borro las columnas duplicadas o que no brindan informacion
        columns_to_drop = ['Satélite', 'Instrumento', 'Cantidad', 'entidad', 'fdc', 'gna', 'gid', 'sag', 'in1','nam']
        merged_data_prov_simpl = merged_data_prov.drop(columns_to_drop, axis=1)
        
        # funciones para generar los graficos en html
        grafico_barra_total_prov(data,path, conf)
        
    # genero dataframe de geopandas para exportar como shape    
    merged_data_prov_geo = gpd.GeoDataFrame(merged_data_prov_simpl, geometry=merged_data_prov['geometry'])
    return merged_data_prov_geo 

def obtener_coordenadas(coordenada):
       
     # Función para extraer latitud y longitud de la cadena de coordenadas
        latitud = -float(coordenada.split('S')[0].replace('[', ''))
        longitud = -float(coordenada.split('S')[1].split('W')[0].replace('[', ''))
        return latitud, longitud
    
def shape_coodenadas(data,coordenadas_str, path, conf):
    
    if 'Mes' in data.columns:
        datos = sinAgrupar_mes(data)  
        # print('datos: ', datos[:4])
             
    else:
        
        datos = sinAgrupar_periodo(data)
        print('no saca graficos, porque es un total de un area seleccionada')
        
    print('las coordenadas de los vertices son; ', coordenadas_str)
    '''     Crear lista de puntos a partir de las coordenadas
     puntos = [Point(obtener_coordenadas(coordenada)) for coordenada in coordenadas]
    Obtener las coordenadas de ambos vértices extremos '''
    coordenadas = []
    partes = coordenadas_str.split("][")
    
    for i in partes:
        valores = re.findall(r'\d+\.?\d*[NS]\d+\.?\d*[WE]', i)
        #print(valores)
        coordenadas_lista = [obtener_coordenadas(valor) for valor in valores]
        coordenadas.append(coordenadas_lista)
    
   # print(coordenadas[0])
    for longitud, latitud in coordenadas[0]:
        longitud1 = longitud
        latitud1 = latitud
        
    for longitud, latitud in coordenadas[1]:
        longitud2 = longitud
        latitud2 = latitud
           
    latitud3 = latitud1
    longitud3 = longitud2
    latitud4 = latitud2
    longitud4 = longitud1
    # print(latitud1, longitud1)
    # print(latitud2, longitud2)
    # Crear polígono a partir de los vértices
   
    poligono = Polygon([(latitud1, longitud1) ,(latitud4,longitud4),( latitud2, longitud2), ( latitud3, longitud3) ])

    # Crear GeoDataFrame con el polígono
    gdf = gpd.GeoDataFrame(geometry=[poligono], crs='EPSG:4326')
    merged_data_geo = gpd.GeoDataFrame(datos, geometry=gdf['geometry'])
   # Guardar el GeoDataFrame como archivo Shapefile
    return merged_data_geo
#-----------------------------------------------------------------------------------------------------------
#---------------- generacion solo de los graficos ----------------------------------------------------------------
def crear_graficos(data , path, codigo, agrupamiento,conf):
    '''funcion que solo procesa los datos para generar los graficos'''
    if codigo == 'Prov':
    
        if agrupamiento == 'Mensual':
            datos = provincia_mes(data)
            grafico_barra_mes_prov(datos, path,conf)
            grafico_lineas_mes_prov(datos, path,conf)
            grafico_heatmap_mes_prov_ind(datos, path, conf)
        
        elif agrupamiento == 'Periodo':
            datos = provincia_periodo(data)
            grafico_barra_total_prov(datos, path, conf)
            
        elif codigo == 'Detalle':    
            print(' datos de detalle')  # Agrega lógica para 'SinAgrupar' si es necesario
            
        else:
            return {'error': 'El archivo proporcionado no es un archivo CSV válido'}, 400   
    
    elif codigo == 'Dpto': 
        if agrupamiento == 'Mensual':
            datos = departamentos_mes(data)
            grafico_barra_mes_depto(datos, path, conf)
            grafico_lineas_mes_depto(datos, path, conf)
            grafico_heatmap_mes_dept_ind(datos, path, conf)
        elif agrupamiento == 'Periodo':
            datos = departamentos_periodo(data)
            grafico_barra_total_depto(datos, path, conf)
           
        elif codigo == 'Detalle':
            print('datos de detalle')  # Agrega lógica para 'SinAgrupar' si es necesario
        else:
            return {'error': 'El archivo proporcionado no es un archivo CSV válido'}, 400 
    
    elif codigo == 'SinAgrupar':   
        print('seleccion del area dibujada por el usuario')
        if agrupamiento == 'Mensual':
            datos= sinAgrupar_mes(data)
            # print(df_sum)
            grafico_barra_mes_sinagrupar(data, path, conf)
            grafico_lineas_mes_sinAgrupar(data, path, conf)
        elif agrupamiento == 'Periodo':
            datos = sinAgrupar_periodo(data)
            print('no saca graficos, porque es un total de un area seleccionada')
        else:
            return {'error': 'El archivo proporcionado no es un archivo CSV válido'}, 400 
         


def crear_html(path_grafico, html_content, path_logo,conf):
    with open(path_grafico, 'w', encoding='utf-8') as file:      
                file.write('<!DOCTYPE html>\n')
                file.write('<html lang="es">\n<head>\n<meta charset="UTF-8">\n<title>Graficos FdC CONAE</title>\n')
                file.write('<script src="https://cdn.plot.ly/plotly-latest.min.js"></script>\n')
                file.write(f'''
                                    
                                        <style>
                                            .datos h3{{
                                                text-align: right;
                                                margin-right: 300px;
                                            }}
                                            .logo-container {{
                                                display: flex;                                                
                                                align-items: center;
                                                margin-left: 250px;
                                                margin-top: 50px;
                                                
                                            }}
                                            .logo-container img {{
                                                margin-right: 50px;  /* Ajusta el margen según sea necesario */
                                                text-align: center;
                                            }}
                                            .logo-container h1 {{
                                                text-align: center;
                                            }}
                                            .grafico {{
                                                display: flex; 
                                            }}
                                        </style>
                                    </head>
                                    <body>
                                        <div class="logo-container">
                                            <img src="{path_logo}" alt="Logo">
                                            <h1> Aplicación de Base de Datos: Focos de Calor </h1>
                                        </div>
                                                                              
                                    
                                ''')
                file.write(html_content)
                file.write(f'''<div class="datos"><h3>Grados de confinaza de los focos de calor : mayor a {conf} </h3><h3> Fuente de información CONAE</h3></div></body>\n</html>''')

def crear_html_aq(path_grafico, html_content, path_logo,conf):
    with open(path_grafico, 'w', encoding='utf-8') as file:      
                file.write('<!DOCTYPE html>\n')
                file.write('<html lang="es">\n<head>\n<meta charset="UTF-8">\n<title>Graficos FdC CONAE</title>\n')
                file.write('<script src="https://cdn.plot.ly/plotly-latest.min.js"></script>\n')
                file.write(f'''
                                    
                                        <style>
                                            .datos h3{{
                                                text-align: right;
                                                margin-right: 300px;
                                            }}
                                            .logo-container {{
                                                display: flex;                                                
                                                align-items: center;
                                                margin-left: 250px;
                                                margin-top: 50px;
                                                
                                            }}
                                            .logo-container img {{
                                                margin-right: 50px;  /* Ajusta el margen según sea necesario */
                                                text-align: center;
                                            }}
                                            .logo-container h1 {{
                                                text-align: center;
                                            }}
                                            .grafico {{
                                                display: flex; 
                                            }}
                                        </style>
                                    </head>
                                    <body>
                                        <div class="logo-container">
                                            <img src="{path_logo}" alt="Logo">
                                            <h1> Aplicación de Base de Datos: Áreas quemadas </h1>
                                        </div>
                                                                              
                                    
                                ''')
                file.write(html_content)
                file.write(f'''<div class="datos"><h3> Fuente de información CONAE</h3></div></body>\n</html>''')

# funciones para generar graficos provincia o departamento 0 Sin agrupar --------------------------------------
# graficos de barra

    
def grafico_barra_mes_prov(data, path, conf):
    #locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
    
    data['Mes'] = pd.to_datetime(data['Mes'], format='%m-%Y')
    # Agrupar por provincia, año y mes, sumando las cantidades
    df_grouped = data.groupby(['Provincia', 'Mes'])['Cantidad'].sum().reset_index()
    df_grouped = df_grouped.sort_values(by='Mes')
    # Crear lista de datos para cada provincia
    data_graficos = []
    for provincia, datos_provincia in df_grouped.groupby('Provincia'):
        barra = go.Bar(
            x=datos_provincia['Mes'][::2],
            y=datos_provincia['Cantidad'],
            name=provincia
        )
        data_graficos.append(barra)
 #verificar si hay solo una provincia para sacar el grafico 
  # y modificar asi el titulo del grafico apra q aparezca el nommbre de la provincia
      
    provincia = df_grouped['Provincia'].unique()
    num_prv = provincia.shape[0]
    print('cantidad de provincias - graficos de barras: ' ,num_prv)
    
    # TEINEDO EN CUENTA Q ME ES IMPOSBLE TRADUCIR LAS FEHCAS AL ESPA;OL
     # Establecer las etiquetas en español para el eje x
    meses_espanol = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
    tickvals = [mes for mes in df_grouped['Mes'].unique() if mes.month % 2 == 1]
    ticktext = [meses_espanol[mes.month - 1] + '-' + str(mes.year) for mes in tickvals]
    
  
    if num_prv > 1 :
        layout = go.Layout(
            #Verificar como hacer para identificar cuando hay mas de una provincias
            title=dict(
                        text=f'Cantidad total de focos de calor por provincia por mes',
                        x=0.5,  # Centrar horizontalmente el título
                        font=dict(size=20)  # Tamaño de la fuente del título
                    ),
            title_font=dict(size=20),
            xaxis=dict(
                    tickvals=tickvals,  # Establecer las etiquetas en el eje x cada 3 valores
                    ticktext=ticktext,  # Etiquetas en español para el eje x
                    automargin=True  # Ajustar automáticamente los márgenes del eje x
                ),
            yaxis=dict(title='Cantidad'),
            #legend=dict(orientation='h', x=0, y=1.1),
            margin=dict(l=40, r=40, t=200, b=40),
            autosize=False,
            width=1500,
            height=900,
        )
    else:
    # Crear layout del gráfico
        provincia = str(data['Provincia'].unique())[2:-2]
        layout = go.Layout(
            #Verificar como hacer para identificar cuando hay mas de una provincias
            # title=f'Cantidad total de focos en la provincia de {provincia}',
            title=dict(
                        text=f'Cantidad total de focos de calor por mes en la provincia de {provincia}',
                        x=0.5,  # Centrar horizontalmente el título
                        font=dict(size=20)  # Tamaño de la fuente del título
                    ),
            title_font=dict(size=20),
            xaxis=dict(
                        tickvals=tickvals,  # Establecer las etiquetas en el eje x cada 3 valores
                        ticktext=ticktext,  # Etiquetas en español para el eje x
                        automargin=True  # Ajustar automáticamente los márgenes del eje x
                    ),
            yaxis=dict(title='Cantidad'),
            #legend=dict(orientation='h', x=0, y=1.1),
            margin=dict(l=40, r=40, t=200, b=40),
            autosize=False,
            width=1500,
            height=900,
            
        )
    
    # Crear figura y plot
    fig = go.Figure(data=data_graficos, layout=layout)
    #path_grafico = f'{path}/{provincia}_grafico_barra.html'
    path_grafico = f'{path}/Total_de_Focos_por_provincia_mes_grafico_barra.html'
    
    #plot(fig, filename=path_grafico, auto_open=False, include_plotlyjs=False)
    # # Generar HTML con la referencia al archivo Plotly.js en el CDN
    html_content = plot(fig, filename=path_grafico, include_plotlyjs=False, output_type='div')
    #html_with_plotly = html_content.replace('<head>', '<head><script src="https://cdn.plot.ly/plotly-latest.min.js"></script>')
    # Guardar el HTML en un archivo
    
    crear_html(path_grafico, html_content, path_logo, conf)
    
   
def grafico_barra_mes_depto(data, path, conf):
    data['Mes'] = pd.to_datetime(data['Mes'], format='%m-%Y')
   # print(data[:3])
    
    provincia = data['Provincia'].unique()
    num_prv = provincia.shape[0]
    print('cantidad de provincias - graficos de barras : ' ,num_prv)
     # TEINEDO EN CUENTA Q ME ES IMPOSBLE TRADUCIR LAS FEHCAS AL ESPA;OL
     # Establecer las etiquetas en español para el eje x
    meses_espanol = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
    
    tickvals = [mes for mes in data['Mes'].unique() if mes.month % 2 == 1]
    ticktext = [meses_espanol[mes.month - 1] + '-' + str(mes.year) for mes in tickvals]
    
    if num_prv > 1 :
        print('no se genrean los graficos porque son muchos las provincias')
    else:
        data_graficos = []
        for prv in provincia:
            df = data[data['Provincia'] == prv]
            
            for depto, datos_deptos in df.groupby('Departamento'):
                barra = go.Bar(
                    x=datos_deptos['Mes'],
                    y=datos_deptos['Cantidad'],
                    name=depto
                )
                data_graficos.append(barra)

                # Crear layout del gráfico
            layout = go.Layout(
                        title=dict(
                            text=f'Cantidad total de focos por departamento de la provincia de {prv}',
                            x=0.5,  # Centrar horizontalmente el título
                            font=dict(size=20)), # Tamaño de la fuente del título
                        title_font=dict(size=20),                            
                        xaxis=dict(
                            tickvals=tickvals,  # Establecer las etiquetas en el eje x cada 3 valores
                            ticktext=ticktext,  # Etiquetas en español para el eje x
                            automargin=True  # Ajustar automáticamente los márgenes del eje x
                        ),
                        yaxis=dict(title='Cantidad'),
                       # legend=dict(orientation='v', x=0, y=1.1),
                        margin=dict(l=40, r=40, t=200, b=40),
                        autosize=False,
                        width=1500,
                        height=900,                        
                    )
            
                    # Crear figura y plot
            fig = go.Figure(data=data_graficos, layout=layout)
            path_grafico = f'{path}/{prv}_total_de_focos_por_departamento_grafico_barra.html'
            #plot(fig, filename=path_grafico, auto_open=False)
           # fig.write_html(path_grafico)
        
             # # Generar HTML con la referencia al archivo Plotly.js en el CDN
            html_content = plot(fig, filename=path_grafico, include_plotlyjs=False, output_type='div')
            
            # Guardar el HTML en un archivo
            crear_html(path_grafico, html_content, path_logo, conf)
           
            

def grafico_barra_mes_sinagrupar(data, path, conf):    
   # print('tabla de inicio en el def barra: ', data[:2])
    data['Mes'] = pd.to_datetime(data['Mes'], format='%m-%Y')
    df_grouped = data.groupby(['Mes'])['Cantidad'].sum().reset_index()
    df_grouped['Mes'] = pd.to_datetime(df_grouped['Mes'], format='%m-%Y')
    #print('tabla de entrada a los graficos:' , df_grouped[:5])
    barra = go.Bar(
            x=df_grouped['Mes'],
            y=df_grouped['Cantidad'],
            name='area'
        )
      # TEINEDO EN CUENTA Q ME ES IMPOSBLE TRADUCIR LAS FEHCAS AL ESPA;OL
     # Establecer las etiquetas en español para el eje x
    meses_espanol = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
    tickvals = [mes for mes in data['Mes'].unique() if mes.month % 2 == 1]
    ticktext = [meses_espanol[mes.month - 1] + '-' + str(mes.year) for mes in tickvals]
    
    # Crear layout del gráfico
    layout = go.Layout(
        #Verificar como hacer para identificar cuando hay mas de una provincias
        # title=f'Cantidad total de focos en la provincia de {provincia}',
        
         title=dict(
                        text=f'Cantidad total de focos de calor por área seleccionada por mes',
                        x=0.5,  # Centrar horizontalmente el título
                        font=dict(size=20)  # Tamaño de la fuente del título
                    ),
        title_font=dict(size=20),
        xaxis=dict(
                        tickvals=tickvals,  # Establecer las etiquetas en el eje x cada 3 valores
                        ticktext=ticktext,  # Etiquetas en español para el eje x
                        automargin=True  # Ajustar automáticamente los márgenes del eje x
                    ),
        yaxis=dict(title='Cantidad'),
        legend=dict(orientation='h', x=0, y=1.1),
        margin=dict(l=40, r=40, t=200, b=40),
        autosize=True,
        width=1500,
        height=900        
    )
    
    # Crear figura y plot
    fig = go.Figure(data=barra, layout=layout)
    #path_grafico = f'{path}/{provincia}_grafico_barra.html'
    path_grafico = f'{path}/Total_de_Focos_por_area_mes_grafico_barra.html'
    
    #plot(fig, filename=path_grafico, auto_open=False)
    # # Generar HTML con la referencia al archivo Plotly.js en el CDN
    html_content = plot(fig, filename=path_grafico, include_plotlyjs=False, output_type='div')
    crear_html(path_grafico, html_content, path_logo, conf)

# #-----------------------------------------------------------------------------------------------------------------
#  Graficos de linea

def grafico_lineas_mes_prov(data, path, conf):
    data['Mes'] = pd.to_datetime(data['Mes'], format='%m-%Y')   
    # Agrupar por provincia, año y mes, sumando las cantidades
   
    df_grouped = data.groupby(['Provincia', 'Mes'])['Cantidad'].sum().reset_index()
    # TEINEDO EN CUENTA Q ME ES IMPOSBLE TRADUCIR LAS FEHCAS AL ESPA;OL
     # Establecer las etiquetas en español para el eje x
    meses_espanol = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
    tickvals = [mes for mes in data['Mes'].unique() if mes.month % 2 == 1]
    ticktext = [meses_espanol[mes.month - 1] + '-' + str(mes.year) for mes in tickvals]
    
    data_graficos = []
    
    fig = go.Figure()
    for provincia, datos_provincia in df_grouped.groupby('Provincia'):
        
        # Crear una línea para cada provincia
        fig.add_trace(go.Scatter(x=datos_provincia['Mes'],
                                 y=datos_provincia['Cantidad'],
                                 mode='lines+markers',
                                 name=provincia))
        data_graficos.append(fig)
    
    provincia = df_grouped['Provincia'].unique()
    num_prv = provincia.shape[0]
    print('cantidad de provincias - graficos de lineas :' ,num_prv)
  #verificar si hay solo una provincia para sacar el grafico 
  # y modificar asi el titulo del grafico apra q aparezca el nommbre de la provincia
  
    if num_prv > 1 :
        fig.update_layout(
                          title=dict(
                                text=f'Cantidad total de focos de calor por provincia por mes',
                                x=0.5,  # Centrar horizontalmente el título
                                font=dict(size=20)  # Tamaño de la fuente del título
                                ),
                        title_font=dict(size=20),
                        xaxis=dict(
                            tickvals=tickvals,  # Establecer las etiquetas en el eje x cada 3 valores
                            ticktext=ticktext,  # Etiquetas en español para el eje x
                            automargin=True  # Ajustar automáticamente los márgenes del eje x
                        ),
                        yaxis_title='Cantidad',
                        legend=dict(x=1.02, y=1),
                        autosize=False,
                        width=1500,
                        height=900,)
    else:
        provincia = str(data['Provincia'].unique())[2:-2]
        fig.update_layout(
                           title=dict(
                        text=f'Cantidad total de focos de calor por mes en la provincia de {provincia}',
                        x=0.5,  # Centrar horizontalmente el título
                        font=dict(size=20)  # Tamaño de la fuente del título
                          ),
                        title_font=dict(size=20),
                        xaxis=dict(
                            tickvals=tickvals,  # Establecer las etiquetas en el eje x cada 3 valores
                            ticktext=ticktext,  # Etiquetas en español para el eje x
                            automargin=True  # Ajustar automáticamente los márgenes del eje x
                        ),
                        yaxis_title='Cantidad',
                        legend=dict(x=1.02, y=1),
                        autosize=False,
                        width=1500,
                        height=900,)
    
    # Guardar el gráfico como un archivo HTML
    #path_grafico = f'{path}/{provincia}_total_de_focos_por_mes_grafico_linea.html'
    path_grafico = f'{path}/Total_de_focos_por_provincia_por__mes_grafico_linea.html'
    html_content = plot(fig, filename=path_grafico, include_plotlyjs=False, output_type='div')
    #fig.write_html(path_grafico)
    crear_html(path_grafico, html_content, path_logo, conf)

def grafico_lineas_mes_depto(data, path, conf):
    data['Mes'] = pd.to_datetime(data['Mes'], format='%m-%Y')
    
    provincia = data['Provincia'].unique()
    num_prv = provincia.shape[0]
    print('cantidad de provincias - graficos de lineas :' ,num_prv)
    # TEINEDO EN CUENTA Q ME ES IMPOSBLE TRADUCIR LAS FEHCAS AL ESPA;OL
     # Establecer las etiquetas en español para el eje x
    meses_espanol = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
    tickvals = [mes for mes in data['Mes'].unique() if mes.month % 2 == 1]
    ticktext = [meses_espanol[mes.month - 1] + '-' + str(mes.year) for mes in tickvals]
    
    if num_prv == 1 :
    
        data_graficos = []
        for prv in provincia:
            df = data[data['Provincia'] == prv]
            fig = go.Figure()
            data_graficos = []
            for depto, datos_deptos in df.groupby('Departamento'):
                    fig.add_trace(go.Scatter(x=datos_deptos['Mes'],
                                            y=datos_deptos['Cantidad'],
                                            mode='lines+markers',
                                            name=depto))
                    
                    data_graficos.append(fig)
            fig.update_layout(
                              title=dict(
                                text=f'Cantidad total de focos por departamento de la provincia de {prv}',
                                x=0.5,  # Centrar horizontalmente el título
                                font=dict(size=20)  # Tamaño de la fuente del título
                                ),
                                xaxis=dict(
                                    tickvals=tickvals,  # Establecer las etiquetas en el eje x cada 3 valores
                                    ticktext=ticktext,  # Etiquetas en español para el eje x
                                    automargin=True  # Ajustar automáticamente los márgenes del eje x
                                ),
                                yaxis_title='Cantidad',
                                legend=dict(x=1.02, y=1),
                                autosize=False,
                                width=1500,
                                height=900,)
            # Guardar el gráfico como un archivo HTML
            path_grafico = f'{path}/{prv}_total_de_focos_por_mes_por_departamento_grafico_linea.html'
                #fig.write_html(path_grafico)
            html_content = plot(fig, filename=path_grafico, include_plotlyjs=False, output_type='div')
            crear_html(path_grafico, html_content, path_logo, conf)
    else: 
        pass
    
def grafico_lineas_mes_sinAgrupar(data, path, conf):
   # locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
    f_grouped = data.groupby(['Mes'])['Cantidad'].sum().reset_index()
   # print(f_grouped[:4])
    
    # TEINEDO EN CUENTA Q ME ES IMPOSBLE TRADUCIR LAS FEHCAS AL ESPA;OL
     # Establecer las etiquetas en español para el eje x
    meses_espanol = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
    tickvals = [mes for mes in data['Mes'].unique() if mes.month % 2 == 1]
    ticktext = [meses_espanol[mes.month - 1] + '-' + str(mes.year) for mes in tickvals]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=f_grouped['Mes'],
                                    y=f_grouped['Cantidad'],
                                    mode='lines+markers',
                                    name='area'))
            
    
    fig.update_layout(
                      title=dict(
                                text=f'Cantidad total de focos de calor por mes en el área seleccionada' ,
                                x=0.5,  # Centrar horizontalmente el título
                                font=dict(size=20)  # Tamaño de la fuente del título
                                ),
                        xaxis=dict(
                                tickvals=tickvals,  # Establecer las etiquetas en el eje x cada 3 valores
                                ticktext=ticktext,  # Etiquetas en español para el eje x
                                automargin=True  # Ajustar automáticamente los márgenes del eje x
                            ),
                        yaxis_title='Cantidad',
                        legend=dict(x=1.02, y=1),
                        autosize=False,
                        width=1500,
                        height=900,)
    # Guardar el gráfico como un archivo HTML
    path_grafico = f'{path}/Total_de_focos_por_mes_por_area_grafico_linea.html'
        #fig.write_html(path_grafico)
    html_content = plot(fig, filename=path_grafico, include_plotlyjs=False, output_type='div')
    crear_html(path_grafico, html_content, path_logo, conf)
    
#----------------------------------------------------------------------------------------------------------------   
#  HEATmap  

 
def grafico_heatmap_mes_prov_ind(data, path, conf):
    #print(data[:10])
    fig_data = []
    provincia = data['Provincia'].unique()
    num_prv = len(provincia)
    print('cantidad de provincias - datos para heatmap: ' ,num_prv)
    #print(data[:3])
    for prv in provincia:
        df = data[data['Provincia'] == prv]
        df.sort_values(by='Mes')
      #  print(df[:10])
        # Crear tabla pivot para el heatmap
        pivot_table = df.pivot_table(index='Año', columns='Mes_Num', values='Cantidad', aggfunc='sum').fillna(0)
        pivot_table_norm = normalizar_datos(pivot_table.values)  # Normalizar los datos
        #print(pivot_table[:3])
        # Crear el heatmap con Plotly
        heatmap = go.Heatmap(z=pivot_table.values.tolist(),
                            # x=pivot_table.columns,
                             x=pivot_table.columns.map(lambda x: data.loc[data['Mes_Num'] == x, 'Meses'].iloc[0]),
                             y=pivot_table.index,
                             colorscale='Reds',
                             colorbar=dict(title='Num. de Focos'))
        
       
        layout = go.Layout(
                           title=dict(
                                text=f'Cantidad de focos por mes y año en la provincia de {prv}',
                                x=0.5,  # Centrar horizontalmente el título
                                font=dict(size=20)  # Tamaño de la fuente del título
                                ),
                           xaxis=dict(title='Mes'),
                           yaxis=dict(title='Año', tickvals=pivot_table.index.astype(int)),
                            autosize=False,
                            width=1500,
                            height=900,)
        
        fig = go.Figure(data=[heatmap], layout=layout)
        
        # Guardar el gráfico como un archivo HTML
        path_grafico = f'{path}/{prv}_mes_por_año_Heatmap.html'
        html_content = plot(fig, filename=path_grafico, include_plotlyjs=False, output_type='div')
        crear_html(path_grafico, html_content, path_logo, conf)
        #-----------------------------------------------
        
    
        if num_prv > 1:
            heatmap_nor = go.Heatmap(
                z=pivot_table_norm.tolist(),
                x=pivot_table.columns.map(lambda x: data.loc[data['Mes_Num'] == x, 'Meses'].iloc[0]),
                y=pivot_table.index,
                colorscale='reds',
                colorbar=dict(title='Valor Normalizado')
            )
            fig_data.append(heatmap_nor)
            # Calcular el número de filas necesarias para tener dos subplots por fila
            num_filas = (len(provincia) + 1) // 2 
            # Crear un trazado con subgráficos verticales y dos columnas
            fig = make_subplots(rows=num_filas, cols=2, shared_xaxes=False, subplot_titles=provincia )

            # Agregar cada heatmap al trazado como un subplot
            for i, heatmap in enumerate(fig_data, start=1):
                # Calcular la fila y la columna para cada subplot
                row = (i - 1) // 2 + 1
                col = (i - 1) %  2+ 1
                fig.add_trace(heatmap, row=row, col=col)

            # Ajustar la altura del layout según la cantidad de subplots
            altura_layout = num_filas * 500  
            fig.update_layout(height=altura_layout) 
            # Ajustar el diseño del trazado
            fig.update_layout(
                title=dict(
                    text=f'Cantidad de Focos de calor con valores Normalizados por mes y año para cada provincias',
                    x=0.5,  # Centrar horizontalmente el título
                    font=dict(size=20)  # Tamaño de la fuente del título
                ),
                coloraxis_colorbar=dict(
                    tickvals=[0, 0.5, 1],
                    ticktext=['Actividad Baja', 'Actividad Media', 'Actividad Alta']
                )
            )

            # Guardar el gráfico como un archivo HTML
            path_grafico = f'{path}/Todas_las_provincia_mes_por_año_Heatmap.html'
            html_content = plot(fig, filename=path_grafico, include_plotlyjs=False, output_type='div')
            crear_html(path_grafico, html_content, path_logo, conf)
        else:
                pass
        
           
def grafico_heatmap_mes_dept_ind(data, path, conf):
    #print(data[:4])
    fig_data = []
    provincia = data['Provincia'].unique()
    periodo  = data['Año'].unique()
    num_prv = len(provincia)
    num_anos = len(periodo)
    print('cantidad de provincias - datos para heatmap: ' ,num_prv)
    print('cantidad de años - datos para heatmap: ' ,num_anos)
    if num_prv > 1 or num_anos < 2 :
        print('NO se generan HEATmap de todas las provincias.')
    #print(data[:3])
    else:
        for prv in provincia:
            df = data[data['Provincia'] == prv]
            departamento = df['Departamento'].unique()
           # print(df[:10])
            for depto in departamento:
                df1 = df[df['Departamento'] == depto]
               # print(depto)
                # Crear tabla pivot para el heatmap
                pivot_table = df1.pivot_table(index='Año', columns='Mes_Num', values='Cantidad', aggfunc='sum').fillna(0)
                # evito normalizar departamentos que no tienen datos
                if pivot_table.empty:
                    print(f'El departamento {depto} en la provincia {prv} no tiene datos.')
                    continue
                pivot_table_norm = normalizar_datos(pivot_table.values)  # Normalizar los datos
               
               # print(pivot_table[:3])
                #-----------------------------------------------
                if num_prv > 1 :
                        
                            pass
                else:
                            heatmap = go.Heatmap(z=pivot_table.values.tolist(),
                                    x=pivot_table.columns.map(lambda x: data.loc[data['Mes_Num'] == x, 'Meses'].iloc[0]),
                                    y=pivot_table.index,
                                    colorscale='Reds',
                                    colorbar=dict(title='Num. de Focos'))
                
            
                            layout = go.Layout(
                                            title=dict(
                                                    text=f'Cantidad de focos por mes y año del departamento de {depto} en la provincia de {prv}',
                                                    x=0.5,  # Centrar horizontalmente el título
                                                    font=dict(size=20)  # Tamaño de la fuente del título
                                                    ),
                                            xaxis=dict(title='Mes'),
                                            yaxis=dict(title='Año', tickvals=pivot_table.index.astype(int)),
                                                autosize=False,
                                                width=1500,
                                                height=900,)
                            
                            fig = go.Figure(data=[heatmap], layout=layout)
                            
                            # Guardar el gráfico como un archivo HTML
                            path_grafico = f'{path}/{depto}_mes_por_año_Heatmap.html'
                            html_content = plot(fig, filename=path_grafico, include_plotlyjs=False, output_type='div')
                            crear_html(path_grafico, html_content, path_logo, conf)
                 # generacion del total de heatmap normalizados           
                heatmap_nor = go.Heatmap(z=pivot_table_norm.tolist(),
                                                x=pivot_table.columns.map(lambda x: data.loc[data['Mes_Num'] == x, 'Meses'].iloc[0]),
                                                y=pivot_table.index,
                                                colorscale='reds',
                                                colorbar=dict(title='Valor Normalizado'),
                                                )
                fig_data.append(heatmap_nor)
                            # Calcular el número de filas necesarias para tener dos subplots por fila
                #num_filas = len(fig_data) // 2 + len(fig_data) % 2
                num_filas = (len(departamento) + 1) // 2        
                            # Crear un trazado con subgráficos verticales y dos columnas
                fig = make_subplots(rows=num_filas, cols=2, shared_xaxes=False, subplot_titles=departamento)
                            
                            # Agregar cada heatmap al trazado como un subplot
                for i, heatmap in enumerate(fig_data, start=1):
                                # Calcular la fila y la columna para cada subplot
                    row = (i - 1) // 2+ 1
                    col = (i - 1) %  2+ 1
                    fig.add_trace(heatmap, row=row, col=col)
                            
                            # Ajustar la altura del layout según la cantidad de subplots
                altura_layout = num_filas * 500  # Ajusta este valor según tus necesidades
                fig.update_layout(height=altura_layout)    
                            # Ajustar el diseño del trazado
                fig.update_layout(
                                    title=dict(
                                    text=f'Cantidad de Focos de calor con valores Normalizados agrupados por departamento por mes y año para cada provincias',
                                    x=0.5,  # Centrar horizontalmente el título
                                    font=dict(size=20)  # Tamaño de la fuente del título
                                         ),
                coloraxis_colorbar=dict(
                    tickvals=[0, 0.5, 1],
                    ticktext=['Actividad Baja', 'Actividad Media', 'Actividad Alta']
                ))
                                            # Ajusta la altura del trazado según la cantidad de provincias
                                                


                            # Guardar el gráfico como un archivo HTML
                path_grafico = f'{path}/Todos_departamentos_de_la_{prv}_por__mes_por_año_Heatmap.html'
                html_content = plot(fig, filename=path_grafico, include_plotlyjs=False, output_type='div')
                crear_html(path_grafico, html_content, path_logo, conf) 
                    
#--------------------------------------------------------------------------
# graficos de datos de periodos --------------------------------------------        
def grafico_barra_total_depto(data, path, conf):
   # provincia = str(data['Provincia'].unique())[2:-2]
    provincia =data['Provincia'].unique()
    desde = str(data['Desde'].unique())[2:-2]
    hasta = str(data['Hasta'].unique())[2:-2]
   
    for prv in provincia:
        filtro = data.loc[data['Provincia']==prv]
        bars = []  # Lista para almacenar las barras
    
    # Iterar sobre los datos y crear una barra para cada fila
        for i, row in filtro.iterrows():
            barra = go.Bar(
                x=[row['Departamento']],
                y=[row['total_focos']],
                name=row['Departamento']
            )
            bars.append(barra)
        
        # Crear layout del gráfico
        
        layout = go.Layout(
                    title=dict(
                        text=f'Cantidad total de focos por departamento de la provincia de {prv} - Periodo desde {desde} hasta {hasta}',
                        x=0.5,  # Centrar horizontalmente el título
                        font=dict(size=20)  # Tamaño de la fuente del título
                    ),
                    #xaxis=dict(title=f'Periodo desde {desde} hasta {hasta}'),
                    yaxis=dict(title='Total de focos'),
                    #legend=dict(orientation='h', x=0, y=1),
                    margin=dict(l=40, r=40, t=200, b=40),
                     autosize=False,
                        width=1500,
                        height=900
                )
        # Crear figura y plot
        fig = go.Figure(data=bars, layout=layout)
        path_grafico = f'{path}/{prv}_Departamentos_grafico_barra.html'
        
        html_content = plot(fig, filename=path_grafico, include_plotlyjs=False, output_type='div')
        crear_html(path_grafico, html_content, path_logo, conf)
    
def grafico_barra_total_prov(data, path, conf):
    desde = str(data['Desde'].unique())[2:-2]
    hasta = str(data['Hasta'].unique())[2:-2]
    bars = []  # Lista para almacenar las barras

    # Iterar sobre los datos y crear una barra para cada fila
    for i, row in data.iterrows():
        barra = go.Bar(
            x=[row['Provincia']],
            y=[row['total_focos']],
            name=row['Provincia']
        )
        bars.append(barra)
        
    
    # Crear layout del gráfico
    layout = go.Layout(
        
        title=dict(
                    text=f'Cantidad total de focos por provincia  - Periodo desde {desde} hasta {hasta}',
                    x=0.5,  # Centrar horizontalmente el título
                    font=dict(size=20)  # Tamaño de la fuente del título
                                ),
        title_font=dict(size=20),
        xaxis=dict(title='Provincias'),
        yaxis=dict(title='Total de focos'),
         margin=dict(l=40, r=40, t=200, b=40),
        autosize=False,
                      width=1500,
                      height=900,
    
    )
    
    # Crear figura y plot
    fig = go.Figure(data=bars, layout=layout)
    path_grafico = f'{path}/focos_de_calor_por_provincias_grafico_barra.html'
    
    html_content = plot(fig, filename=path_grafico, include_plotlyjs=False, output_type='div')
    crear_html(path_grafico, html_content, path_logo, conf)


#-----------------------------------------------------
# funciones de generacion de shpae para areas quemadas

def procesamiento_AQ(data):
        
        AQ_ha = data['area_quemada_ha'].sum()
        AQ_ha_per = data['porcentaje_quemado'].sum()
         
        
        data['mes'] = pd.to_datetime(data['mes']).dt.strftime('%Y-%m')    
        
        
        # lista de nombres de los departamentos
        lista_deptos = data.loc[:, ['nombre_prov','nombre_dpto', 'in1']].drop_duplicates(subset=['in1'])
        #print(lista_deptos[:4])
       
        # Crear la tabla pivote para el área quemada
        pivot_area_quemada = data.pivot_table(index='in1', columns='mes', values='area_quemada_ha', aggfunc='sum')
        
        #print(pivot_area_quemada[:5])
      
        # Crear la tabla pivote para el porcentaje quemado
        pivot_porcentaje_quemado = data.pivot_table(index='in1', columns='mes', values='porcentaje_quemado', aggfunc='sum')

            
        # print(df_sum[:4])
        #print(lista_deptos)
       # lo mergeo con el listado de nombres de departamentos porque se habia pedido al hacer el group
        merged_depto_aq = pivot_area_quemada.merge(lista_deptos, on='in1', how='inner')
        merged_depto_pc = pivot_porcentaje_quemado.merge(lista_deptos, on='in1', how='inner')
        # print(merged_data_depto.dtypes)
        # print(dept.dtypes)
        merged_depto_aq['in1'] = merged_depto_aq['in1'].astype(str) 
        merged_depto_pc['in1'] = merged_depto_pc['in1'].astype(str) 
        
        
        totalAQ_fin = pivot_area_quemada.sum().sum()
        totalPC_fin = pivot_porcentaje_quemado.sum().sum()
        print('total de AQ ha al inicio: ', AQ_ha)
        print('prov total de AQ al final: ', totalAQ_fin)  
        print('total de AQ porce. inicio: ', AQ_ha_per) 
        print('prov total de AQ procentaje al final: ', totalPC_fin) 
        return merged_depto_aq, merged_depto_pc

def shape_focos_AQ(data, dept):
        merged_depto_aq , merged_depto_pc = procesamiento_AQ(data) 
        
       # print('prov total de AQ porcentaje al final: ', totalAQ_finpor)  
        # print(merged_data_depto.dtypes)
        # print(dept.dtypes)
        dept['in1'] = dept['in1'].astype(str) 
        merged_data_depto_aq = pd.merge(merged_depto_aq, dept, left_on='in1', right_on='in1', how='inner')
        merged_data_depto_pc = pd.merge(merged_depto_pc, dept, left_on='in1', right_on='in1', how='inner')
        merged_data_depto_aq_geo = gpd.GeoDataFrame(merged_data_depto_aq, geometry=merged_data_depto_aq['geometry'])
        merged_data_depto_pc_geo = gpd.GeoDataFrame(merged_data_depto_pc, geometry=merged_data_depto_aq['geometry'])
        
        return merged_data_depto_aq_geo, merged_data_depto_pc_geo

def grafico_mes_prov_AQ(data, path):
   # print(data[:4])
   # locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
    conf = ''
    data['mes'] = pd.to_datetime(data['mes'])
    # Agrupar por provincia, año y mes, sumando las cantidades
    df_grouped = data.groupby(['nombre_prov', 'mes'])['area_quemada_ha'].sum().reset_index()
    df_grouped = df_grouped.sort_values(by='mes')
    # Crear lista de datos para cada provincia
    data_graficos = []
    for provincia, datos_provincia in df_grouped.groupby('nombre_prov'):
        barra = go.Bar(
            x=datos_provincia['mes'],
            y=datos_provincia['area_quemada_ha'],
            name=provincia
        )
        data_graficos.append(barra)
 #verificar si hay solo una provincia para sacar el grafico 
  # y modificar asi el titulo del grafico apra q aparezca el nommbre de la provincia
      
    provincia = df_grouped['nombre_prov'].unique()
    num_prv = provincia.shape[0]
    print('cantidad de provincias - graficos de barras: ' ,num_prv)
    
    # TEINEDO EN CUENTA Q ME ES IMPOSBLE TRADUCIR LAS FEHCAS AL ESPA;OL
     # Establecer las etiquetas en español para el eje x
    meses_espanol = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
    tickvals = [mes for mes in df_grouped['mes'].unique() if mes.month % 2 == 1]
    ticktext = [meses_espanol[mes.month - 1] + '-' + str(mes.year) for mes in tickvals]
    
  
    if num_prv > 1 :
        layout = go.Layout(
            #Verificar como hacer para identificar cuando hay mas de una provincias
            title=dict(
                        text=f'Cantidad total del área quemada por provincia por mes (en ha)',
                        x=0.5,  # Centrar horizontalmente el título
                        font=dict(size=20)  # Tamaño de la fuente del título
                    ),
            title_font=dict(size=20),
            xaxis=dict(
                    tickvals=tickvals,  # Establecer las etiquetas en el eje x cada 3 valores
                    ticktext=ticktext,  # Etiquetas en español para el eje x
                    automargin=True  # Ajustar automáticamente los márgenes del eje x
                ),
            yaxis=dict(title='Total de ha'),
            #legend=dict(orientation='h', x=0, y=1.1),
            margin=dict(l=40, r=40, t=200, b=40),
            autosize=False,
            width=1500,
            height=900,
        )
    else:
        prov = str(df_grouped['nombre_prov'].unique())[2:-2]
        layout = go.Layout(
            #Verificar como hacer para identificar cuando hay mas de una provincias
            title=dict(
                        text=f'Cantidad total del área quemada de la provincia de {prov} por mes (en ha)',
                        x=0.5,  # Centrar horizontalmente el título
                        font=dict(size=20)  # Tamaño de la fuente del título
                    ),
            title_font=dict(size=20),
            xaxis=dict(
                    tickvals=tickvals,  # Establecer las etiquetas en el eje x cada 3 valores
                    ticktext=ticktext,  # Etiquetas en español para el eje x
                    automargin=True  # Ajustar automáticamente los márgenes del eje x
                ),
            yaxis=dict(title='total de ha'),
            #legend=dict(orientation='h', x=0, y=1.1),
            margin=dict(l=40, r=40, t=200, b=40),
            autosize=False,
            width=1500,
            height=900,
        )
    
    # Crear figura y plot
    fig = go.Figure(data=data_graficos, layout=layout)
    #path_grafico = f'{path}/{provincia}_grafico_barra.html'
    path_grafico = f'{path}/Total_AQ_por_provincia_mes_grafico_barra.html'
    
    #plot(fig, filename=path_grafico, auto_open=False, include_plotlyjs=False)
    # # Generar HTML con la referencia al archivo Plotly.js en el CDN
    html_content = plot(fig, filename=path_grafico, include_plotlyjs=False, output_type='div')
    #html_with_plotly = html_content.replace('<head>', '<head><script src="https://cdn.plot.ly/plotly-latest.min.js"></script>')
    # Guardar el HTML en un archivo
    
    crear_html_aq(path_grafico, html_content, path_logo, conf)
    
def grafico_mes_prov_AQpc(data, path):
   # print(data[:4])
   #locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
    conf = ''
    data['mes'] = pd.to_datetime(data['mes'])
    # Agrupar por provincia, año y mes, sumando las cantidades
    df_grouped = data.groupby(['nombre_prov', 'mes'])['porcentaje_quemado'].sum().reset_index()
    df_grouped = df_grouped.sort_values(by='mes')
    # Crear lista de datos para cada provincia
    data_graficos = []
    for provincia, datos_provincia in df_grouped.groupby('nombre_prov'):
        barra = go.Bar(
            x=datos_provincia['mes'],
            y=datos_provincia['porcentaje_quemado'],
            name=provincia
        )
        data_graficos.append(barra)
 #verificar si hay solo una provincia para sacar el grafico 
  # y modificar asi el titulo del grafico apra q aparezca el nommbre de la provincia
      
    provincia = df_grouped['nombre_prov'].unique()
    num_prv = provincia.shape[0]
   # print('cantidad de provincias - graficos de barras: ' ,num_prv)
    
    # TEINEDO EN CUENTA Q ME ES IMPOSBLE TRADUCIR LAS FEHCAS AL ESPA;OL
     # Establecer las etiquetas en español para el eje x
    meses_espanol = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
    tickvals = [mes for mes in df_grouped['mes'].unique() if mes.month % 2 == 1]
    ticktext = [meses_espanol[mes.month - 1] + '-' + str(mes.year) for mes in tickvals]
    
  
    if num_prv > 1 :
        layout = go.Layout(
            #Verificar como hacer para identificar cuando hay mas de una provincias
            title=dict(
                        text=f'Porcentaje del área quemada por provincia por mes',
                        x=0.5,  # Centrar horizontalmente el título
                        font=dict(size=20)  # Tamaño de la fuente del título
                    ),
            title_font=dict(size=20),
            xaxis=dict(
                    tickvals=tickvals,  # Establecer las etiquetas en el eje x cada 3 valores
                    ticktext=ticktext,  # Etiquetas en español para el eje x
                    automargin=True  # Ajustar automáticamente los márgenes del eje x
                ),
            yaxis=dict(title='Porcentaje'),
            #legend=dict(orientation='h', x=0, y=1.1),
            margin=dict(l=40, r=40, t=200, b=40),
            autosize=False,
            width=1500,
            height=900,
        )
    else:
        prov = str(df_grouped['nombre_prov'].unique())[2:-2]
        layout = go.Layout(
            #Verificar como hacer para identificar cuando hay mas de una provincias
            title=dict(
                        text=f'Porcentaje del área quemada de la provincia de {prov} por mes (en ha)',
                        x=0.5,  # Centrar horizontalmente el título
                        font=dict(size=20)  # Tamaño de la fuente del título
                    ),
            title_font=dict(size=20),
            xaxis=dict(
                    tickvals=tickvals,  # Establecer las etiquetas en el eje x cada 3 valores
                    ticktext=ticktext,  # Etiquetas en español para el eje x
                    automargin=True  # Ajustar automáticamente los márgenes del eje x
                ),
            yaxis=dict(title='Porcentaje'),
            #legend=dict(orientation='h', x=0, y=1.1),
            margin=dict(l=40, r=40, t=200, b=40),
            autosize=False,
            width=1500,
            height=900,
        )
    
    # Crear figura y plot
    fig = go.Figure(data=data_graficos, layout=layout)
    #path_grafico = f'{path}/{provincia}_grafico_barra.html'
    path_grafico = f'{path}/Total_AQPC_por_provincia_mes_grafico_barra.html'
    
    #plot(fig, filename=path_grafico, auto_open=False, include_plotlyjs=False)
    # # Generar HTML con la referencia al archivo Plotly.js en el CDN
    html_content = plot(fig, filename=path_grafico, include_plotlyjs=False, output_type='div')
    #html_with_plotly = html_content.replace('<head>', '<head><script src="https://cdn.plot.ly/plotly-latest.min.js"></script>')
    # Guardar el HTML en un archivo
    
    crear_html_aq(path_grafico, html_content, path_logo, conf)
    
    
###--------------------------------------------------------------------------
#borradores de graficos
def grafico_barra_mes_prov1(data, path, conf):
    data_pivot = data
    # Crear lista de datos para cada provincia
    data_graficos = []
    for provincia in data_pivot['Provincia'].unique():
        barra = go.Bar(
            x=data_pivot.columns[2:],  # Ignorar las columnas 'Mes' y 'Provincia'
            y=data_pivot[data_pivot['Provincia'] == provincia].values.tolist()[0][2:],  # Obtener los valores de la fila de la provincia
            name=provincia
        )
        data_graficos.append(barra)

    # Verificar la cantidad de provincias para ajustar el título del gráfico
    num_prv = data_pivot['Provincia'].nunique()

    if num_prv > 1:
        layout_title = f'Cantidad total de focos de calor por provincia por mes'
    else:
        provincia = data_pivot['Provincia'].unique()[0]
        layout_title = f'Cantidad total de focos de calor por mes en la provincia de {provincia}'
    
    # Crear layout del gráfico
    layout = go.Layout(
        title=dict(
            text=layout_title,
            x=0.5,
            font=dict(size=20)
        ),
        xaxis=dict(title='Mes'),
        yaxis=dict(title='Cantidad'),
        margin=dict(l=40, r=40, t=200, b=40),
        autosize=False,
        width=1500,
        height=900,
    )

    # Crear figura y plot
    fig = go.Figure(data=data_graficos, layout=layout)
    path_grafico = f'{path}/Total_de_Focos_por_provincia_mes_grafico_barra222.html'
    
    html_content = plot(fig, filename=path_grafico, include_plotlyjs=False, output_type='div')
    
    crear_html(path_grafico, html_content, path_logo, conf)