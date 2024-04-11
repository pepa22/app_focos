# -*- coding: utf-8 -*-
__author__ = 'JosefinaOtero'

""" aplicacion original que esta subida en el servidor donde se mejoro la 
nomenclarutra de los archivos.
En el archivo de funciones estan desarrolladas las funciones para generar los gaficos de 
los datos agrupads por provincia y de[artamento.
Modificacion de la respuesta para solo enviar el archivo zip en determida situacion
Modificaciones para generar shape y graficos para las areas quemadas
Se usaron las versiones app_v8 y funciones_v8
Se saco la definicion de local utf8, se agregaron los heatmaps"""

import os
from flask import Flask, request, jsonify, make_response, render_template
import zipfile

import geopandas as gpd
from funciones import *
import json
import glob
import re   


# Obtener la fecha actual
fecha_actual = datetime.now()



app = Flask(__name__)

# Formatear la fecha según la configuración regional
fecha_formateada = fecha_actual.strftime('%A, %d de %B de %Y, %H:%M:%S')
print("Fecha de inicio de la aplicacion:", fecha_formateada)

# Lee la configuración desde el archivo JSON
with open('config.json') as config_file:
    config = json.load(config_file)

# Usa las configuraciones en tu aplicación
BASE_DIR = config["BASE_DIR"]
UPLOAD_FOLDER_FOCOS = os.path.join(BASE_DIR, config["UPLOAD_FOLDER_FOCOS"])
RESULTS_FOLDER_FOCOS = os.path.join(BASE_DIR, config["RESULTS_FOLDER_FOCOS"])
UPLOAD_FOLDER_AQ = os.path.join(BASE_DIR, config["UPLOAD_FOLDER_AQ"])
RESULTS_FOLDER_AQ = os.path.join(BASE_DIR, config["RESULTS_FOLDER_AQ"])
SHAPES_FOLDER = os.path.join(BASE_DIR, config["SHAPES_FOLDER"])
DEBUG_MODE = config.get("DEBUG_MODE", False)
HOST = config.get("HOST", "0.0.0.0")
#PORT = config.get("PORT", 8000)


crear_carpeta(UPLOAD_FOLDER_FOCOS)
crear_carpeta(RESULTS_FOLDER_FOCOS)

app.config['UPLOAD_FOLDER_FOCOS'] = UPLOAD_FOLDER_FOCOS
app.config['RESULTS_FOLDER_FOCOS'] = RESULTS_FOLDER_FOCOS
app.config['UPLOAD_FOLDER_AQ'] = UPLOAD_FOLDER_AQ
app.config['RESULTS_FOLDER_AQ'] = RESULTS_FOLDER_AQ
app.config['RESULTS_FOLDER_AQ'] = SHAPES_FOLDER

crear_carpeta(UPLOAD_FOLDER_AQ)
crear_carpeta(RESULTS_FOLDER_FOCOS)
#-------------------------------------------------------------------
# funciones de procesamiento

def enviar_zip(result_zip_filepath, process_results_folder):
    zip_data = b''  # Inicializar como byte
    with open(result_zip_filepath, 'rb') as f:
            zip_data = f.read()

    '''teniendo el return detro del bucle da un archivo compilado de los focos, 
    si lo saco genero un shape por cada satelite. 
    Devolver el resultado y el código de estado 200 en caso de éxito '''
    
    return zip_data, 200 

def procesar_archivo_zip(zip_filepath, extract_folder, RESULTS_FOLDER):
    print('procesando el archivo zip')
    try:
        with zipfile.ZipFile(zip_filepath, 'r') as zip_ref:
            zip_ref.extractall(extract_folder)
            nombre_original = os.path.splitext(os.path.basename(zip_filepath))[0]
            
        if carpeta_vacia(extract_folder):
            return {'error': f'La carpeta {extract_folder} está vacía.'}, 400
        else:
            focos = glob.glob(os.path.join(extract_folder, '*.csv'))
            
            process_results_folder = os.path.join(RESULTS_FOLDER, 'processed_results')
            crear_carpeta(process_results_folder)
            
            # Inicializar zip_data fuera del bucle
            data = leer_csv(focos) 
            #print(data[:3])
            return data, nombre_original, process_results_folder
    except Exception as e:
       eliminar_carpeta(extract_folder) 
       ''' verificar si poniendo esta linea d eodigo aca, borra la carpeta si no se completa la 
       desacarga o se produce un error en el procesamineto'''
       return {'error': str(e)}, 500 

'''Se crean los shape a nivel provincia o departamento segun se requiera con agrupaciones por mes o periodo.'''
def crear_shapes(data, process_results_folder, nombre_original, codigo, conf):
        ## Leer shape base para comparar
            prov_shapefile_path = os.path.join(SHAPES_FOLDER, 'provincia.shp')
            prov = gpd.read_file(prov_shapefile_path)
            dept_shapefile_path = os.path.join(SHAPES_FOLDER, 'departamento.shp')
            dept = gpd.read_file(dept_shapefile_path)
            #print('leyendo shape')
            
            #print(codigo)
            if codigo == 'Prov':
                    merged_data_geo = shape_focos_prov(data, prov, process_results_folder, conf)
            elif codigo == 'Dpto':
                    merged_data_geo = shape_focos_depto(data, dept, process_results_folder, conf)
            elif codigo == 'SinAgrupar':
                    print('sin agrupar')  
                    
                    patron = r'\[\d+\.?\d*[NS]\d+\.?\d*[WE]\]\[\d+\.?\d*[NS]\d+\.?\d*[WE]\]'
                    coincidencias = re.findall(patron, nombre_original)
                    coord = coincidencias[-1]
                    merged_data_geo = shape_coodenadas(data, coord, process_results_folder, conf)
                    
            output_shapefile = os.path.join(process_results_folder, f'{nombre_original}.shp')
            merged_data_geo.to_file(output_shapefile, driver='ESRI Shapefile')
            #result_zip_filepath = os.path.join(RESULTS_FOLDER, f'{nombre_original}.zip')
            
            return merged_data_geo

''' funciones para el procesamiento de areas quemadas se generan los graficos y dos archivos shape, 
a nivel de departamento con datos de prov para total de heacteras y procentaje de areas quemadas.'''

def crear_shapes_aq(data, process_results_folder,nombre_original):
            ## Leer shape base para comparar
            
            dept_shapefile_path = os.path.join(SHAPES_FOLDER, 'departamento.shp')
            dept = gpd.read_file(dept_shapefile_path)
            
            #genero los respectivos shape
           
            merged_data_depto_aq_geo, merged_data_depto_pc_geo = shape_focos_AQ(data, dept)
            
            output_shapefile_depto_aq = os.path.join(process_results_folder, f'{nombre_original}_depto_aq.shp')
            merged_data_depto_aq_geo.to_file(output_shapefile_depto_aq, driver='ESRI Shapefile')
            output_shapefile_depto_pc = os.path.join(process_results_folder, f'{nombre_original}_depto_pc.shp')
            merged_data_depto_pc_geo.to_file(output_shapefile_depto_pc, driver='ESRI Shapefile')
            
            # return merged_data_geo_depto, merged_data_geo_prov
            return merged_data_depto_aq_geo, merged_data_depto_pc_geo


#-----------------------------------------------------------------------

@app.route('/upload_zip', methods=['POST'])
def upload_zip():
    if 'file' not in request.files:
        return jsonify({'error': 'No se proporcionó ningún archivo ZIP'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No se seleccionó ningún archivo'}), 400

    if not file.filename.endswith('.zip'):
        return jsonify({'error': 'El archivo proporcionado NO es un archivo ZIP válido'}), 400
   
        
    zip_filepath = os.path.join(app.config['UPLOAD_FOLDER_FOCOS'], file.filename)
    file.save(zip_filepath)

    extract_folder = os.path.join(app.config['UPLOAD_FOLDER_FOCOS'], 'extracted')
    crear_carpeta(extract_folder)

    eliminar_carpeta(extract_folder)
    
    
    data, nombre_original, process_results_folder = procesar_archivo_zip(zip_filepath, extract_folder, RESULTS_FOLDER_FOCOS)
    nombre_archivo = os.path.splitext(os.path.basename(nombre_original))[0]
    
    # este patron acepta valores que tengan o no decimales
    patron = r'\[\d+\.?\d*[NS]\d+\.?\d*[WE]\]\[\d+\.?\d*[NS]\d+\.?\d*[WE]\]'

    coincidencias = re.findall(patron, nombre_original)
    print(coincidencias)
    # Tomamos la última coincidencia encontrada
    if coincidencias:
        coord = coincidencias[-1]
        print("coordenadas:", coord)
        nombre_archivo_sin_patron = nombre_original.replace(coord, "")
        print(nombre_archivo_sin_patron)
        codigo = nombre_archivo_sin_patron.split('_')[-1]
        print('el codigo del archivo es : ', codigo)
        agrupamiento = nombre_archivo_sin_patron.split('_')[-2]
        conf = nombre_archivo_sin_patron.split('_')[4][4:]
        print('la confianza del archivo es : ', conf)
        print('agrupamiento de los datos: ', agrupamiento)
    else:
        print("No se encontraron coordenadas")       
        
        codigo = nombre_archivo.split('_')[-1]
        print('el codigo del archivo es : ', codigo)
        agrupamiento = nombre_archivo.split('_')[-2]
        conf = nombre_archivo.split('_')[4][4:]
        print('la confianza del archivo es : ', conf)
        print('agrupamiento de los datos: ', agrupamiento)
    
    #parametro pasado en la url para quereconozca si quiero o no procesar los shape
    
    #shp_param = request.args.get('shp') # se activa esta linea d codigo cuando le paso el script a pablo 
                                        # porque si aplicacion toma el parametro de la url y no del form como yo
    shp_param = request.form.get('shp')
    #print(shp_param)
    if shp_param and shp_param.lower() == 'no':
            # se generan solo los graficos          
            crear_graficos(data, process_results_folder, codigo, agrupamiento, conf)
            print('se generaron solo los gaficos - ok')
            result_zip_filepath = os.path.join(RESULTS_FOLDER_FOCOS, f'{nombre_original}.zip')
            crear_zip(process_results_folder, result_zip_filepath)
            
            result = enviar_zip(result_zip_filepath, process_results_folder)
            response = make_response(result)
            response.headers['Content-Disposition'] = 'attachment; filename=' + file.filename
            os.remove(result_zip_filepath)              
            eliminar_carpeta(process_results_folder)
            return response
    else:
            crear_shapes(data, process_results_folder,nombre_original, codigo, conf)
            crear_graficos(data, process_results_folder, codigo, agrupamiento, conf)
            #print(process_results_folder)
            result_zip_filepath = os.path.join(RESULTS_FOLDER_FOCOS, f'{nombre_original}.zip')
            crear_zip(process_results_folder, result_zip_filepath)
                 # Eliminar el archivo ZIP después de enviarlo como respuesta
            
           # crear el archivo zip para todo el poducto
            result = enviar_zip(result_zip_filepath, process_results_folder)
            response = make_response(result)
            response.headers['Content-Disposition'] = 'attachment; filename=' + file.filename
            os.remove(result_zip_filepath)              
            eliminar_carpeta(process_results_folder)
            return response
    
        
@app.route('/upload_zipAQ', methods=['POST'])
def upload_zipAQ():
    if 'file' not in request.files:
        return jsonify({'error': 'No se proporcionó ningún archivo ZIP'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No se seleccionó ningún archivo'}), 400

    if not file.filename.endswith('.zip'):
        return jsonify({'error': 'El archivo proporcionado NO es un archivo ZIP válido'}), 400
   
        
    zip_filepath = os.path.join(app.config['UPLOAD_FOLDER_AQ'], file.filename)
    file.save(zip_filepath)

    extract_folder = os.path.join(app.config['UPLOAD_FOLDER_AQ'], 'extracted')
    crear_carpeta(extract_folder)

    eliminar_carpeta(extract_folder)
    
    
    data, nombre_original, process_results_folder = procesar_archivo_zip(zip_filepath, extract_folder, RESULTS_FOLDER_AQ)
    nombre_archivo = os.path.splitext(os.path.basename(nombre_original))[0]
        
    print(nombre_archivo)    
      
    #parametro pasado en la url para quereconozca si quiero o no procesar los shape
    
    #shp_param = request.args.get('shp') # se activa esta linea d codigo cuando le paso el script a pablo 
                                        # porque si aplicacion toma el parametro de la url y no del form como yo
    shp_param = request.form.get('shp')
    #print(shp_param)
    if shp_param and shp_param.lower() == 'no':
                      
            grafico_mes_prov_AQ(data, process_results_folder)
            grafico_mes_prov_AQpc(data, process_results_folder)
            
            print('se generaron los graficos ok')
            result_zip_filepath = os.path.join(RESULTS_FOLDER_AQ, f'{nombre_original}.zip')
            crear_zip(process_results_folder, result_zip_filepath)
            
            result = enviar_zip(result_zip_filepath, process_results_folder)
            response = make_response(result)
            response.headers['Content-Disposition'] = 'attachment; filename=' + file.filename
            os.remove(result_zip_filepath)              
            eliminar_carpeta(process_results_folder)
            return response
            pass
    else:
            crear_shapes_aq(data, process_results_folder,nombre_original)
            grafico_mes_prov_AQ(data, process_results_folder)
            grafico_mes_prov_AQpc(data, process_results_folder)
            
            #print(process_results_folder)
            result_zip_filepath = os.path.join(RESULTS_FOLDER_AQ, f'{nombre_original}.zip')
            crear_zip(process_results_folder, result_zip_filepath)
                 # Eliminar el archivo ZIP después de enviarlo como respuesta
            
           # crear el archivo zip para todo el poducto
            result = enviar_zip(result_zip_filepath, process_results_folder)
            response = make_response(result)
            response.headers['Content-Disposition'] = 'attachment; filename=' + file.filename
            os.remove(result_zip_filepath)              
            eliminar_carpeta(process_results_folder)
            return response
  
          
        
@app.route('/focosAPP')
def mostrar_descarga(name=None):
   
    return render_template('formulario.html', name=name)

@app.route('/areasQuemadasAPP')
def mostrar_descarga_Aq(name=None):
   
    return render_template('formularioAQ.html', name=name)

if __name__ == '__main__':
    
    app.run(debug=True, host='0.0.0.0', port=8080)
    # Formatear la fecha según la configuración regional
    fecha_formateada = fecha_actual.strftime('%A, %d de %B de %Y : %H:%M:%S')
    print("Fecha de cierre de la aplicacion:", fecha_formateada)



