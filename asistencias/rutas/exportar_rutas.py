from flask import request
from flask import make_response
from flask import render_template

from asistencias import app
from asistencias import csrf
from asistencias.helpers import db_ejecutar
from asistencias.helpers import generar_excel_wb
from asistencias.helpers import login_requerido
from asistencias.helpers import validar_clases
from asistencias.helpers_asistencia import *

from tempfile import NamedTemporaryFile
from tempfile import TemporaryDirectory

import os
import random
import string
import shutil

@app.route("/exportar")
@login_requerido
def exportar():
	"""pagina exportar asistencia a excel"""

	return render_template("exportar.html")

@app.route("/exportar-excel", methods=["POST"])
@login_requerido
@csrf.exempt
def exportar_excel():

	"""
		exporta la asistencia a excel a partir de la informacion especificada

		la ruta recibe JSON con la siguiente informacion:

		'usar_rango' -- verdadero o falso. Define si se ultilizara un rango de fechas.
						en caso de ser falso. Se asume el uso de 'periodo'.

		'fecha_inicial' -- string en formato YYYY-MM-DD. requerido si 'usar_rango' es verdadero.
		'fecha_final' -- string en formato YYYY-MM-DD. requerido si 'usar_rango' es verdadero.

		'periodo' -- string. requerido si 'usar_rango' es falso. 
		
					periodos implementados: hoy, ultima_semana, ultimo_mes,
					ultimo_dia. Este ultimo representa el ultimo dia 
					que la asistencia de cada clase fue guardada.

		'clases' -- lista de clases (diccionarios) con keys 'nombre' e 'id'.

		la ruta crea un archivo zip el cual contiene
		un archivo excel por cada asistencia de cada clase.

		la ruta devuelve una respuesta con la representacion
		binaria del archivo zip.

	"""

	clases = []
	asistencia_clases = []

	try:

		info = request.get_json()
		clases = info["clases"]
		clases = validar_clases(clases)

		clases_id = [clase["id"] for clase in clases]

		usar_rango = info["usar_rango"]

		if not usar_rango:

			periodo = info["periodo"]
			periodos_validos = ["hoy", "ultimo_dia", "ultima_semana", "ultimo_mes"]

			if periodo not in periodos_validos:
				raise ValueError(f"Periodo invalido. periodos validos: {periodos_validos}")

			asistencia_clases = asistencia_desde_periodo(periodo, clases_id)

		else:

			# convertir las fechas proporcionadas a tiempo unix
			tiempos = fechas_a_unix(info["fecha_inicial"], info["fecha_final"])

			if not tiempos:
				raise ValueError("Fecha(s) en formato incorrecto. formato: 'YYYY-MM-DD'")

			t1_unix, t2_unix = tiempos

			asistencia_clases = asistencia_desde_rango(t1_unix, t2_unix, clases_id)

	except (KeyError, ValueError) as e:
		return f"JSON en formato incorrecto. Error {e}", 400
	except Exception as e:
		print(e)
		return f"Error {e}", 400

	for asistencia in asistencia_clases:
		
		for alumno in asistencia:

			presente = alumno["presente"]
			estado = ""

			if presente:
				estado = "Presente"
			else:
				estado = "Ausente"
				alumno["tiempo"] = ""

			alumno["estado"] = estado

	# directorio temporal
	with TemporaryDirectory() as temp_dir:

		titulos = ["Alumno", "Carnet", "Estado", "Fecha", "Tiempo"]
		keys    = ["nombre", "carnet", "estado", "fecha", "tiempo"]

		for i in range(len(asistencia_clases)):

			asistencia = asistencia_clases[i]
			wb = generar_excel_wb(titulos=titulos, keys=keys, elementos=asistencia)
			clase_nombre = clases[i]["nombre"]

			# guardar excel en el directorio temporal
			wb.save(temp_dir + f"/{clase_nombre}.xlsx")

		zip_nombre = "".join([random.choice(string.ascii_lowercase) for i in range(8)])

		# crear zip del directorio
		dir_zip  = shutil.make_archive(zip_nombre, "zip", temp_dir)

		with open(dir_zip, "rb") as f:
			res = make_response(f.read())

		try:
			os.remove(dir_zip)
		except Exception as e:
			print(e)
			raise Exception(e)

		return res

@app.route("/exportar-excel-json", methods=["POST"])
@login_requerido
@csrf.exempt
def exportar_json_excel():

	"""exporta la asistencia proporcionada a excel

		la asistencia se proporciona en formato JSON
		la asistencia es una lista de diccionarios.

		estos diccionarios representan a los alumnos.
		cada diccionario debe tener las keys:

		'fecha' -- string en formato YYYY-MM-DD. 
					representa la fecha de asistencia del alumno.

		'tiempo' -- string en formato HH:MM:SS. 
					representa el tiempo de asistencia del alumno.

		'presente' -- entero (1 o 0). determina si el alumno esta presente o no. 
	"""

	asistencia = request.get_json()

	if not asistencia:
		return "JSON 'asistencia' faltante", 400

	try:

		for alumno in asistencia:

			t_unix = alumno["fecha"]
			presente = int(alumno["presente"])

			if presente not in [1, 0]:
				raise ValueError("'presente' no se encuentra en (1, 0)")

			alumno["estado"] = "Presente" if presente else "Ausente"

	except (KeyError, ValueError, TypeError) as e:
		return f"JSON 'asistencia' en formato incorrecto. Error: {e}", 400 

	titulos = ["Alumno", "Carnet", "Estado", "Fecha", "Tiempo"]
	keys    = ["nombre", "carnet", "estado", "fecha", "tiempo"]

	wb = generar_excel_wb(titulos=titulos, keys=keys, elementos=asistencia)

	with NamedTemporaryFile() as tmp:
		wb.save(tmp.name)
		tmp.seek(0)
		res = make_response(tmp.read())
		return res