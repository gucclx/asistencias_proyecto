from flask import request, redirect, session, jsonify
from asistencias.helpers import login_requerido, db_ejecutar, \
								es_admin

from asistencias.helpers_asistencia import *
from asistencias import app
from asistencias import csrf

@app.route("/listas")
@login_requerido
def devolver_lista():

	"""devuelve una lista de 10 elementos de la base de datos

		args:

		'categoria' : string. la categoria deseada.
						categorias implementadas: 'profesor', 'alumno', 'clase'

		'busqueda' : string. busqueda que se desea realizar.
					e.g. "Alice", "Fisica"
	"""
	
	cat = request.args.get("categoria")
	busqueda = request.args.get("busqueda")

	if not cat or not busqueda:
		return "Categoria o busqueda faltante", 400

	cat_validas = ["profesor", "alumno", "clase"]
	
	if cat not in cat_validas:
		return f"""La categoria no es valida. 
					Categorias: {cat_validas}""", 400

	busqueda = busqueda.strip()
	busqueda = "%" + busqueda + "%"

	if cat == "profesor":
		return jsonify(db_ejecutar("""
				SELECT nombre, id 
				FROM Profesores 
				WHERE nombre LIKE (?) LIMIT 10""", busqueda))

	elif cat == "alumno":
		return jsonify(db_ejecutar("""
				SELECT nombre, carnet 
				FROM Alumnos 
				WHERE nombre LIKE (?) LIMIT 10""", busqueda))

	elif cat == "clase":
		admin = es_admin(session["user_id"])
		if admin:
			return jsonify(db_ejecutar("""
				SELECT nombre, id 
				FROM clases 
				WHERE nombre LIKE (?) LIMIT 10""", busqueda))
		else:
			return jsonify(db_ejecutar("""
					SELECT Clases.nombre, Clases.id 
					FROM Clases
					JOIN Clase_Profesor ON Clase_Profesor.clase_id = Clases.id 
					AND Clase_Profesor.prof_id = (?)
					WHERE Clases.nombre LIKE (?) LIMIT 10""", 
					session["user_id"], busqueda))


@app.route("/listas-asistencia", methods=["POST"])
@login_requerido
@csrf.exempt
def devolver_asistencia():

	"""devuelve una lista de asistencia a partir de la informacion especificada.
		la ruta recibe JSON con la siguiente informacion:

		'usar_rango' : boolean. determina si usar un rango de fechas.
						en caso de ser falso, se asume el uso de 'periodo'.

		'fecha_inicial' -- string en formato YYYY-MM-DD. requerido si 'usar_rango' es verdadero.
		'fecha_final' -- string en formato YYYY-MM-DD. requerido si 'usar_rango' es verdadero.

		'periodo' -- string. requerido si 'usar_rango' es falso. 
		
					periodos implementados: hoy, ultima_semana, ultimo_mes,
					ultimo_dia. Este ultimo representa el ultimo dia 
					que la asistencia de cada clase fue guardada.

		'clase_id' -- entero. id de la clase de donde se obtendra la asistencia.
	"""
	try:

		info = request.get_json()

		usar_rango = info["usar_rango"]
		clase_id = int(info["clase_id"])

		if not usar_rango:

			periodo = info["periodo"]
			periodos_validos = ["hoy", "ultimo_dia", "ultima_semana", "ultimo_mes"]

			if periodo not in periodos_validos:
				raise ValueError(f"Periodo invalido. periodos validos: {periodos_validos}")

			asistencia = asistencia_desde_periodo(periodo, [clase_id])[0]
			return jsonify(asistencia)

		else:

			# usar un rango de tiempo
			tiempos = fechas_a_unix(info["fecha_inicial"], info["fecha_final"])

			if not tiempos:
				raise ValueError("Fecha(s) en formato incorrecto. formato: 'YYYY-MM-DD'")

			t1_unix, t2_unix = tiempos;

			asistencia = asistencia_desde_rango(t1_unix, t2_unix, [clase_id])[0]

			return jsonify(asistencia)

	except (KeyError, TypeError, ValueError) as e:
		return f"JSON en formato invalido, error: {e}", 400
	except Exception as e:
		print(e)
		return f"error: {e}", 400


@app.route("/listas-asistencia-hoy")
@login_requerido
def devolver_asistencia_hoy():

	"""devuelve la lista de asistencia de hoy apartir de la informacion especificada.
		se devuelve la lista de los alumnos de la clase
		si el dia de hoy no posee asistencia de la clase especificada.

		GET args:
		'clase_id' : entero. id de la clase de donde se obtendra la asistencia de hoy.
	"""
	
	clase_id = request.args.get("clase_id")

	if not clase_id:
		return "Parametro 'clase_id' faltante", 404

	try:
		clase_id = int(clase_id)
	except ValueError as e:
		return f"El id de la clase debe ser entero. Error{e}", 404

	admin = es_admin(session["user_id"])

	if not admin:

		q = db_ejecutar("""
			SELECT *
			FROM Clase_Profesor
			WHERE clase_id = (?)
			AND prof_id = (?)
			""", clase_id, session["user_id"])

		# que la clase sea del profesor
		if not q:
			return "", 400

	asistencia = asistencia_desde_periodo("hoy", [clase_id])[0]

	asistencia_tmp = set()

	for alumno in asistencia:
		asistencia_tmp.add(alumno["nombre"])

	alumnos_clase = db_ejecutar("""
		SELECT Alumnos.nombre, Alumnos.carnet 
		FROM Alumnos 
		JOIN Clase_Alumno 
		ON Clase_Alumno.clase_id = (?)
		AND Clase_Alumno.alumno_carnet = carnet""", clase_id)

	hoy = ""

	hoy = db_ejecutar("""SELECT date(strftime('%s', 'now', 'localtime', 'start of day'), 'unixepoch')
							as fecha""")[0]["fecha"]

	for alumno in alumnos_clase:
		if alumno["nombre"] not in asistencia_tmp:
			alumno["fecha"] = hoy
			alumno["tiempo"] = "00:00:00"
			alumno["presente"] = 0
			asistencia.append(alumno)

	return jsonify(asistencia)
