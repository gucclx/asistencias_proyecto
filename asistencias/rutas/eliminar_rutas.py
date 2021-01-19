from flask import flash
from flask import request
from flask import render_template
from flask import redirect
from flask import session
from flask import url_for

from asistencias.forms import EliminarEntradaForm
from asistencias.forms import ClasePersonaForm
from asistencias.helpers import *
from asistencias import app

import json

# pagina eliminar entrada (profesor, alumno, etc)
@app.route("/eliminar-entrada", methods=["GET", "POST"])
@login_requerido
@admin_requerido
def eliminar_entrada():

	form = EliminarEntradaForm()

	if form.validate_on_submit():

		cat = form.categoria.data
		entrada = form.nombre.data.strip()

		if cat == "clase":
			q = db_ejecutar("""SELECT * 
								FROM Clases 
								WHERE nombre = (?)""", entrada)
			if not q:
				flash("La clase no existe", "warning")
				return redirect(url_for("eliminar_entrada"))

			db_ejecutar("""DELETE FROM Clases
							WHERE nombre = (?)""", entrada)

		elif cat == "alumno":
			q = db_ejecutar("""SELECT * 
								FROM Alumnos 
								WHERE nombre = (?)""", entrada)
			if not q:
				flash("El alumno no existe", "warning")
				return redirect(url_for("eliminar_entrada"))

			db_ejecutar("""DELETE FROM Alumnos
							WHERE nombre = (?)""", entrada)
		elif cat == "profesor":
			q = db_ejecutar("""SELECT * 
								FROM Clases 
								WHERE nombre = (?)""", entrada)
			if not q:
				flash("El profesor no existe", "warning")
				redirect(url_for("eliminar_entrada"))

			db_ejecutar("""DELETE 
							FROM Profesores
							WHERE nombre = (?)""", entrada)

		tenia_que_ser_espanol = "o" if cat != "clase" else "a"
		flash(f"{cat.title()} eliminad{tenia_que_ser_espanol}", "info")

		return redirect(url_for("eliminar_entrada"))

	return render_template("eliminar_entrada.html", form=form)

# pagina eliminar alumno/profesor de una clase
@app.route("/eliminar-alumno-clase", endpoint="e-alumno", methods=["GET", "POST"])
@app.route("/eliminar-profesor-clase", endpoint="e-profesor", methods=["GET", "POST"])
@login_requerido
def eliminar_clase_persona():

	if request.endpoint == "e-profesor":
		admin = es_admin(session["user_id"])
		if not admin:
			return "admin requerido", 403

	form = ClasePersonaForm()

	if form.validate_on_submit():

		clases = request.form.get("clases")

		# el form no provee las clases
		if not clases:
			return "JSON 'clases' faltante", 400

		clases = json.loads(clases)
		clases = validar_clases(clases)

		if not clases:
			flash("Debe seleccionar al menos una clase", "warning")
			return url_for(request.endpoint)

		cat = ""
		persona_id = -1
		persona_nombre = form.persona.data.strip()

		if request.endpoint == "e-alumno":
			cat = "alumno"
			persona_id = db_ejecutar("""
					SELECT carnet FROM Alumnos 
					WHERE nombre = (?)""", persona_nombre)
		else:
			cat = "profesor"
			persona_id = db_ejecutar("""
					SELECT id FROM Profesores 
					WHERE nombre = (?)""", persona_nombre)

		if not persona_id:
			flash(f"El {cat} no existe", "warning")
			return url_for(request.endpoint)

		num_clases = len(clases)
		clases_id = [clase["id"] for clase in clases]
		phs = ", ".join(["?"] * num_clases)

		# lista de clases que el alumno posee
		# o el profesor ensena
		validas_id = []

		if cat != "alumno":
			persona_id = persona_id[0]["id"]
			validas_id = db_ejecutar(f"""
							SELECT clase_id 
							FROM Clase_Profesor
							WHERE clase_id IN ({phs})
							AND prof_id = (?)""", 
							*clases_id, persona_id)
		else:
			persona_id = persona_id[0]["carnet"]
			validas_id = db_ejecutar(f"""
							SELECT clase_id 
							FROM Clase_Alumno 
							WHERE clase_id IN ({phs})
							AND alumno_carnet = (?)""", 
							*clases_id, persona_id)

		validas_id = [clase["clase_id"] for clase in validas_id]
		no_eliminadas = []

		# filtrar clases no validas
		# i.e. el alumno no posee tales clases/
		# el profesor no ensena tales clases
		
		index = num_clases - 1
		while index >= 0:
			if clases_id[index] not in validas_id:
				no_eliminadas.append(clases[index]["nombre"])
				clases_id.pop(index)
			index -= 1

		if clases_id:
			
			clases_persona = []
			clases_persona = [(_id, persona_id) for _id in clases_id]
			q = ""

			if cat == "alumno":
				q = """DELETE FROM Clase_Alumno 
						WHERE clase_id = (?) 
						AND alumno_carnet = (?)"""
			else:
				q = """DELETE FROM Clase_Profesor 
						WHERE clase_id = (?) 
						AND prof_id = (?)"""

			db_ejecutar(q, clases_persona, many=True)

			eliminadas = ", ".join([clase["nombre"] for clase in clases])
			flash(f"{cat.title()} eliminado de {eliminadas}", "info")

		if no_eliminadas:
			no_eliminadas_contador = len(no_eliminadas)
			if cat == "profesor":
				flash(f"""Profesor no eliminado de {no_eliminadas_contador} 
						clase(s) porque no las enseña""", "warning")
			else:
				flash(f"""Alumno no eliminado de {no_eliminadas_contador} 
						clase(s) porque no se encuentra en estas""", "warning")

		return url_for(request.endpoint)

	cat = ""
	if request.endpoint == "e-alumno":
		cat = "alumno"
	elif request.endpoint == "e-profesor":
		cat = "profesor"

	form.persona.label.text = f"Nombre del {cat}:"
	form.clase.label.text = f"Clase(s) del {cat}:"

	return render_template("e_persona_clase.html", form=form, cat=cat)