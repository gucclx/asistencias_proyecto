from flask import (request, render_template, 
					redirect, session, flash, url_for)
from asistencias.helpers import *
from asistencias.forms import ClaseForm, ClasePersonaForm, NuevoNombreClase
from asistencias import app
import json

# pagina registro de clases
@app.route("/registrar-clase", methods=["GET", "POST"])
@login_requerido
@admin_requerido
def registrar_clase():

	form = ClaseForm()

	if form.validate_on_submit():

		clase_nombre = form.nombre.data.strip()
		prof_nombre = form.profesor.data.strip()

		clase = db_ejecutar("""
			SELECT nombre 
			FROM Clases 
			WHERE nombre = (?)""", clase_nombre)

		if clase:
			flash("El nombre de la clase ya existe", "info")
			return redirect(url_for("registrar_clase"))

		db_ejecutar("""
			INSERT INTO Clases (nombre, fecha)
			VALUES (?, strftime('%s', 'now', 'localtime'))""", 
			clase_nombre)

		clase_id = db_ejecutar("""
						SELECT id 
						FROM Clases
						WHERE nombre = (?)""", clase_nombre)

		if not clase_id:
			return "La clase no existe", 404

		clase_id = clase_id[0]["id"]

		if prof_nombre:

			prof_id = db_ejecutar("""
					SELECT id 
					FROM Profesores 
					WHERE nombre = (?)""", prof_nombre)

			if not prof_id:
				flash("El profesor no existe.", "warning")
				return redirect(url_for("registrar_clase"))

			prof_id = prof_id[0]["id"]

			db_ejecutar("""
				INSERT INTO Clase_Profesor (clase_id, prof_id) 
				VALUES (?, ?)""", clase_id, prof_id)

		flash(f"Clase {clase_nombre} registrada", "info")
		return redirect(url_for("registrar_clase"))
		
	return render_template("r_clase.html", form=form)

# pagina mis clases/lista de clases
@app.route("/mis-clases", endpoint="mis-clases")
@app.route("/listas-clase", endpoint="listas-clase")
@login_requerido
def clase_listas():

	if request.endpoint == "listas-clase":

		admin = es_admin(session["user_id"])
		if not admin:
			return "admin requerido", 400

	clases = []
	title  = ""

	if request.endpoint == "mis-clases":
		clases = db_ejecutar("""
					SELECT nombre, id
					FROM Clases
					JOIN Clase_Profesor
					ON id = clase_id
					WHERE prof_id = (?)""", 
					session["user_id"])
		title  = "Mis clases"
	else:
		clases = db_ejecutar("""
					SELECT nombre, id
					FROM Clases""")
		title  = "Clases"


	return render_template("clase_listas.html", clases=clases, title=title)

# pagina detalles de una clase
@app.route("/clase-detalle")
@login_requerido
def clase_detalle():
	
	clase_id = request.args.get("clase_id")

	admin = es_admin(session["user_id"])
	clase_info = []

	if admin:
		clase_info = db_ejecutar("""
				SELECT Clases.nombre, datetime(Clases.fecha, 'unixepoch') as fecha
				FROM Clases 
				WHERE Clases.id = (?)""", clase_id)

		if not clase_info:
			return "Clase inexistente", 400
	else:
		clase_info = db_ejecutar("""
					SELECT Clases.nombre, datetime(Clases.fecha, 'unixepoch') as fecha
					FROM Clases 
					JOIN Clase_Profesor
					ON Clase_Profesor.clase_id = Clases.id
					AND Clase_Profesor.prof_id = (?)
					WHERE Clases.id = (?)""", 
					session["user_id"], clase_id)

		if not clase_info:
			return "Accion no autorizada/clase inexistente", 400

	profesor = db_ejecutar("""
					SELECT Profesores.nombre, Profesores.id 
					FROM Profesores
					JOIN Clase_Profesor 
					ON Profesores.id = Clase_Profesor.prof_id
					AND Clase_Profesor.clase_id = (?)""", 
					clase_id)

	tiene_profesor = True
	
	if profesor:
		if profesor[0]["id"] == session["user_id"]:
			profesor = "Yo"
		else:
			profesor = profesor[0]["nombre"]
	else:
		profesor = "Ningún profesor"
		tiene_profesor = False
	
	alumnos = db_ejecutar("""
					SELECT Alumnos.nombre, Alumnos.carnet
					FROM Alumnos
					JOIN Clase_Alumno
					ON Clase_Alumno.clase_id = (?)
					AND Clase_Alumno.alumno_carnet = Alumnos.carnet""", clase_id)

	info = {
		"nombre" : clase_info[0]["nombre"],
		"profesor" : profesor,
		"tiene_profesor" : tiene_profesor,
		"fecha" : clase_info[0]["fecha"],
		"alumnos_total" : len(alumnos)
	}

	return render_template("clase_detalle.html", info=info, alumnos=alumnos)

# pagina reemplazar el nombre de una clase
@app.route("/reemplazar-nombre-clase", methods=["GET", "POST"])
@login_requerido
def reemplazar_nombre_clase():

	form = NuevoNombreClase()

	if form.validate_on_submit():

		nombre = form.clase.data.strip()

		admin = es_admin(session["user_id"])

		clase = []

		if admin:
			clase = db_ejecutar("""
				SELECT id 
				FROM Clases 
				WHERE nombre = (?)""", nombre)

			if not clase:
				flash("Clase inexistente", "warning")
				return redirect(url_for("reemplazar_nombre_clase"))
		else:
			clase = db_ejecutar("""
				SELECT Clases.id 
				FROM Clases
				JOIN Clase_Profesor
				ON Clase_Profesor.clase_id = Clases.id
				AND Clase_Profesor.prof_id = (?)
				WHERE nombre = (?)""", nombre, session["user_id"])

			if not clase:
				flash("Clase inexistente/Acción denegada", "warning")
				return redirect(url_for("reemplazar_nombre_clase"))

		nuevo_nombre = form.nombre.data.strip()
		
		db_ejecutar("""
			UPDATE Clases 
			SET nombre = (?)
			WHERE id = (?)""", nuevo_nombre, clase[0]["id"])

		flash("Operación exitosa", "info")
		return redirect(url_for("reemplazar_nombre_clase"))

	return render_template("nombre_clase.html", form=form)


# pagina agregar alumno/profesor a una clase
@app.route("/agregar-alumno-clase", endpoint="a-alumno", methods=["GET", "POST"])
@app.route("/agregar-profesor-clase", endpoint="a-profesor",  methods=["GET", "POST"])
@login_requerido
def clase_persona():

	if request.endpoint == "a-profesor": 
		filas = db_ejecutar("""
			SELECT admin 
			FROM Profesores 
			WHERE id = (?)""", session["user_id"])

		if not filas:
			return "Usuario inexistente.", 404

		if filas[0]["admin"] == 0:
			return "admin requerido", 403

	form = ClasePersonaForm()

	if form.validate_on_submit():

		clases = request.form.get("clases")

		# no se proveen las clases
		if not clases:
			return "", 400

		clases = json.loads(clases)

		clases = validar_clases(clases)
		
		if not clases:
			flash("Debe seleccionar al menos una clase", "warning")
			return url_for(request.endpoint), 400

		cat = ""
		persona_id = -1;
		persona_nombre = form.persona.data.strip()

		if request.endpoint == "a-alumno":
			cat = "alumno"
			persona_id = db_ejecutar("""
							SELECT carnet 
							FROM Alumnos 
							WHERE nombre = (?)""", 
							persona_nombre)
		else:
			cat = "profesor"
			persona_id = db_ejecutar("""
							SELECT id 
							FROM Profesores
							WHERE nombre = (?)""", 
							persona_nombre)

		if not persona_id:
			flash(f"El {cat} no existe", "warning")
			return url_for(request.endpoint)

		num_clases = len(clases)
		clases_id = [clase["id"] for clase in clases]
		phs = ", ".join(["?"] * num_clases)

		# clases en las que el alumno ya se encuentra
		# o el profesor ya ensena
		no_validas_id = []

		if cat == "alumno":
			persona_id = persona_id[0]["carnet"]
			no_validas_id = db_ejecutar(f"""SELECT clase_id
											FROM Clase_Alumno 
											WHERE clase_id IN ({phs}) 
											AND alumno_carnet = (?)""", 
											*clases_id, persona_id)
		else:
			persona_id = persona_id[0]["id"]
			no_validas_id = db_ejecutar(f"""SELECT clase_id
											FROM Clase_Profesor
											WHERE clase_id IN ({phs})""", 
											*clases_id)

		no_validas_id = [clase_id["clase_id"] for clase_id in no_validas_id]
		no_registradas_contador = 0

		# filtrar clases validas
		# i.e. el alumno ya se encuentra en tales clases/
		# el prof ya ensena tales clases
		
		index = num_clases - 1
		while index >= 0:
			if clases_id[index] in no_validas_id:
				no_registradas_contador += 1
				clases_id.pop(index)
			index -= 1

		if clases_id:

			# lista de tuplas para la funcion sqlite executemany
			clases_persona = []
			clases_persona = [(_id, persona_id) for _id in clases_id]

			if cat == "alumno":
				q = f"""INSERT INTO Clase_Alumno (clase_id, alumno_carnet) 
						VALUES (?, ?)"""

			elif cat == "profesor":
				q = f"""INSERT INTO Clase_Profesor (clase_id, prof_id) 
						VALUES (?, ?)"""

			db_ejecutar(q, clases_persona, many=True)

			cantidad = len(clases_id)
			flash(f"{cat.title()} agregado a {cantidad} clase(s)", "info")

		if no_registradas_contador > 0:

			if cat == "profesor":
				flash(f"""Profesor no agregado a {no_registradas_contador} 
							clase(s) porque estas se encuentran ocupadas""", "warning")
			else:
				flash(f"""El alumno no fue agregado a {no_registradas_contador} 
							clase(s) porque ya se encuentra en estas""", "warning")

		return url_for(request.endpoint)

	cat = ""
	if request.endpoint == "a-alumno":
		cat = "alumno"
	elif request.endpoint == "a-profesor":
		cat = "profesor"

	form.persona.label.text = f"Nombre del {cat}:"
	form.clase.label.text = "Seleccione una o más clases:"
	endpoint = url_for(request.endpoint)
	return render_template("clase_persona.html", form=form, cat=cat, endpoint=endpoint)