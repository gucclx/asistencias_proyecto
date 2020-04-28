from flask import (request, render_template, 
					redirect, session, flash, url_for, make_response)
from asistencias.helpers import *
from asistencias.helpers_asistencia import asistencia_desde_periodo
from asistencias.forms import AsistenciaForm
from asistencias import app
from datetime import datetime
import time
import json

# pagina tomar asistencia
@app.route("/asistencia", methods=["GET", "POST"])
@login_requerido
def asistencia():

	form = AsistenciaForm()

	admin = es_admin(session["user_id"])
	clases = []

	if not admin:
		clases = db_ejecutar("""
					SELECT nombre, id FROM Clases
					JOIN Clase_Profesor ON id = clase_id
					WHERE prof_id = (?)""", session["user_id"])
	else:
		clases = db_ejecutar("""
					SELECT nombre, id 
					FROM Clases""")

	if not clases:
		form.clases.choices.append((-1, "Ninguna clase"))
	else:
		for clase in clases:
			form.clases.choices.append((clase["id"], clase["nombre"]))

	if form.validate_on_submit():

		clase_id = form.clases.data
		alumnos  = request.form.get("alumnos")

		if not alumnos:
			return "JSON 'alumnos' faltante", 400

		if clase_id <= 0:
			flash("Seleccione una clase", "warning")
			return url_for("asistencia")

		prof_id = session["user_id"]
		admin = es_admin(prof_id)

		if not admin:

			q = db_ejecutar("""
				SELECT * FROM Clase_Profesor
				WHERE clase_id = (?)
				AND prof_id = (?)""", clase_id, prof_id)

			# verificar que la clase sea del profesor
			if not q:
				return "Clase no autorizada", 400

		alumnos = json.loads(alumnos)

		if not alumnos:
			flash("La clase no posee estudiantes", "warning")
			return url_for("asistencia")
		
		try:
			
			for alumno in alumnos:

				if not isinstance(alumno["carnet"], str):
					raise TypeError

				if not isinstance(alumno["fecha"], str):
					raise TypeError

				if not isinstance(alumno["tiempo"], str):
					raise TypeError

				if alumno["presente"] not in [0, 1]:
					raise ValueError("val 'presente' no se encuentra en (0, 1)")

				datetime_string = " ".join([alumno["fecha"], alumno["tiempo"]])

				fecha = datetime.strptime(datetime_string, "%Y-%m-%d %H:%M:%S").timestamp()
				fecha += -time.timezone

				alumno["fecha"] = fecha

		except (ValueError, KeyError, TypeError) as e:
			return f"JSON 'alumnos' en formato incorrecto. Error: {e}", 400

		asistencia = []

		hoy = db_ejecutar("""SELECT strftime('%s', 'now', 'localtime', 'start of day')
								as fecha""")[0]["fecha"]
		for alumno in alumnos:
			asistencia.append(
				(clase_id, alumno["carnet"], alumno["presente"], alumno["fecha"], hoy)
			)
		
		db_ejecutar("""
			INSERT INTO Asistencias (clase_id, alumno_carnet, presente, fecha, asistencia_fecha)
			VALUES (?, ?, ?, ?, ?)
			ON CONFLICT (asistencia_fecha, clase_id, alumno_carnet)
			DO UPDATE SET presente = excluded.presente, fecha = excluded.fecha""",
			asistencia, many=True)

		flash("Asistencia guardada", "info")
		return url_for("asistencia")

	return render_template("asistencia.html", form=form)

# pagina lista de asistencia
@app.route("/asistencia-lista")
@login_requerido
def asistencia_lista():

	admin = es_admin(session["user_id"])
	clases = []

	if admin:
		clases = db_ejecutar("""SELECT nombre, id 
								FROM Clases""")
	else:
		clases = db_ejecutar("""
				SELECT nombre, id FROM Clases 
				JOIN Clase_Profesor ON clase_id = id 
				AND prof_id = (?)""", session["user_id"])

	return render_template("asistencia_lista.html", clases=clases)