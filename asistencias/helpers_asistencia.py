from asistencias.helpers import db_ejecutar
from datetime import datetime
import time

def asistencia_desde_periodo(periodo, clases_id):

	"""Genera y retorna la asistencia de las clases especificadas
		a partir del periodo especificado.

		args:

		periodo -- String. Periodo deseado. Periodos implementados: hoy, ultima_semana, ultimo_mes,
								ultimo_dia. Este ultimo representa el ultimo dia 
								que la asistencia de cada clase fue guardada.

		clases_id -- Lista de ids (enteros) de cada clase.
	"""

	fecha_inicial = 0
	fecha_final   = 0

	if periodo == "hoy":

		fecha_inicial = db_ejecutar("""SELECT strftime('%s', 'now', 'localtime', 'start of day')
										as fecha""")[0]["fecha"]

		fecha_final   = db_ejecutar("""SELECT strftime('%s', 'now', 'localtime', 'start of day', '+86399 seconds')
										as fecha""")[0]["fecha"]

	elif periodo == "ultima_semana":

		fecha_inicial = db_ejecutar("""SELECT strftime('%s', 'now', 'localtime', 'start of day', '-7 days')
										as fecha""")[0]["fecha"]

		fecha_final = db_ejecutar("""SELECT strftime('%s', 'now', 'localtime', 'start of day', '+86399 seconds')
										as fecha""")[0]["fecha"]

	elif periodo == "ultimo_mes":

		fecha_inicial = db_ejecutar("""SELECT strftime('%s', 'now', 'localtime', 'start of day', '-1 month')
										as fecha""")[0]["fecha"]

		fecha_final = db_ejecutar("""SELECT strftime('%s', 'now', 'localtime', 'start of day', '+86399 seconds')
										as fecha""")[0]["fecha"]

	if periodo != "ultimo_dia":
		return asistencia_desde_rango(fecha_inicial, fecha_final, clases_id)


	# conseguir ultima fecha de cada clase
	ultimas_fechas = []
	tmp = []

	for clase_id in clases_id:
		ultima_fecha = db_ejecutar("""
			SELECT max(asistencia_fecha) as fecha
			FROM asistencias 
			WHERE clase_id = (?)""", clase_id)

		if ultima_fecha:
			ultimas_fechas.append(ultima_fecha[0]["fecha"])
			tmp.append(clase_id)
			
	# solo las clases que tengan algun registro de asistencia
	clases_id = tmp

	# conseguir asistencia de cada fecha
	clases_asistencia = []
	for fecha, clase_id in zip(ultimas_fechas, clases_id):
		asistencia = db_ejecutar("""
						SELECT Alumnos.nombre, Alumnos.carnet, Asistencias.presente, 
										date(Asistencias.fecha, 'unixepoch') as fecha, 
										time(Asistencias.fecha, 'unixepoch') as tiempo
						FROM Alumnos 
						JOIN Asistencias 
						ON Asistencias.fecha >= (?) 
						AND Alumnos.carnet = alumno_carnet 
						WHERE clase_id = (?)""", fecha, clase_id)

		clases_asistencia.append(asistencia)

	return clases_asistencia

def asistencia_desde_rango(t1_unix, t2_unix, clases_id):

	"""Retorna la asistencia guardada dentro del rango de tiempo especificado,
		de las clases especificadas.

		args:

		t1_unix -- Entero. Representa le fecha inicial en tiempo unix.
		t2_unix -- Entero. Representa la fecha final en tiempo unix.
		clases_id -- lista de ids (enteros) de las clases.
	"""

	clases_asistencia = []

	for clase_id in clases_id:
		asistencia = db_ejecutar("""
					SELECT Alumnos.nombre, Alumnos.carnet, Asistencias.presente,
									date(Asistencias.fecha, 'unixepoch') as fecha, 
									time(Asistencias.fecha, 'unixepoch') as tiempo
					FROM Alumnos
					JOIN Asistencias 
					ON Asistencias.fecha BETWEEN (?) AND (?)
					AND Asistencias.alumno_carnet = Alumnos.carnet
					WHERE Asistencias.clase_id = (?)""", 
					t1_unix, t2_unix, clase_id)

		clases_asistencia.append(asistencia)

	return clases_asistencia

def fechas_a_unix(f1, f2):

	"""Retorna una lista de tiempos unix.

		args:

		f1 -- String en formato YYYY-MM-DD
		f2 -- String en formato YYYY-MM-DD
	"""

	try:
		if not isinstance(f1, str) or not isinstance(f2, str):
			raise TypeError
		
		t1_unix = datetime.strptime(f1, "%Y-%m-%d").timestamp() - time.timezone
		t2_unix = datetime.strptime(f2, "%Y-%m-%d").timestamp() - time.timezone
		return t1_unix, t2_unix

	except (TypeError, ValueError) as e:
		print(e)
		return None