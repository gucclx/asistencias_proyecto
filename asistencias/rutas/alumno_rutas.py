from flask import flash
from flask import request
from flask import render_template
from flask import redirect
from flask import url_for

from asistencias.forms import AlumnoForm
from asistencias import app
from asistencias.helpers import *

import json

# pagina registrar alumno
@app.route("/registrar-alumno", methods=["GET", "POST"])
@login_requerido
def registrar_alumno():

	form = AlumnoForm()

	if form.validate_on_submit():

		alumno_nombre = form.nombre.data.strip()
		carnet = form.carnet.data.strip()

		carnet_existente = db_ejecutar("""
				SELECT nombre, carnet 
				FROM Alumnos
				WHERE carnet = (?)""", carnet)

		if carnet_existente:

			flash("El carnet ya existe", "warning")
			return url_for("registrar_alumno")

		db_ejecutar("""
			INSERT INTO Alumnos (nombre, carnet) 
			VALUES (?, ?)""", 
			alumno_nombre, carnet)

		clases = request.form.get("clases")

		if clases:
			clases = json.loads(clases)
			clases = validar_clases(clases)

			if clases:
				clases_alumno = [(clase["id"], carnet) for clase in clases]
				db_ejecutar("""
					INSERT INTO Clase_Alumno (clase_id, alumno_carnet) 
					VALUES (?, ?)""", clases_alumno, many=True)

		flash(f"Alumno {alumno_nombre} registrado exitosamente", "info")
		return url_for("registrar_alumno")

	return render_template("r_alumno.html", form=form)