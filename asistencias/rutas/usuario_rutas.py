from flask import flash
from flask import make_response
from flask import request
from flask import render_template
from flask import redirect
from flask import session
from flask import url_for

from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash

from asistencias.forms import *
from wtforms.validators import Regexp
from asistencias.helpers import *
from asistencias import app

# pagina administrar cuenta
@app.route("/administrar")
@login_requerido
def administrar():

	datos = db_ejecutar("""SELECT nombre, usuario, id, admin 
							FROM Profesores 
							WHERE id = (?)""", session["user_id"])
	if not datos:
		return "usuario inexistente", 404

	nombre = datos[0]["nombre"]
	usuario = datos[0]["usuario"]
	es_admin = datos[0]["admin"]

	clases_profesor = db_ejecutar("""
						SELECT clase_id 
						FROM Clase_Profesor 
						WHERE prof_id = (?)""", datos[0]["id"])

	clases_total = len(clases_profesor)

	phs = ", ".join(["?"] * clases_total)
	clases_id = [clase["clase_id"] for clase in clases_profesor]

	q = f"""SELECT DISTINCT alumno_carnet 
			FROM Clase_Alumno 
			WHERE clase_id IN ({phs})"""

	alumnos = db_ejecutar(q, *clases_id)

	info = {
		"usuario" : usuario,
		"nombre" : nombre,
		"clases_total" : clases_total,
		"alumnos_total" : len(alumnos),
		"es_admin" : es_admin
	}
	
	return render_template("administrar.html", info=info)

# pagina cambiar datos
@app.route("/cambiar-nombre", endpoint="cambiar-nombre", methods=["GET", "POST"])
@app.route("/cambiar-usuario", endpoint="cambiar-usuario", methods=["GET", "POST"])
@app.route("/cambiar-pswd", endpoint="cambiar-pswd", methods=["GET", "POST"])
@login_requerido
def cambiar_dato():

	form = ""
	cat = ""

	if request.endpoint == "cambiar-pswd":
		form = CambiarPswdForm()
		cat = "contraseña"
	else:
		form = CambiarDatosForm()

	if request.endpoint == "cambiar-nombre":
		cat = "nombre"
		form.dato_nuevo.validators = [Regexp(persona_nombre_regex, message=nombre_invalido_persona),
										Regexp(len_regex, message=len_invalida)]

	elif request.endpoint == "cambiar-usuario":
		cat = "usuario"
		form.dato_nuevo.validators = [Regexp(usuario_regex, message=usuario_invalido),
										Regexp(len_regex, message=len_invalida)]

	if form.validate_on_submit():

		user_hash = db_ejecutar("""SELECT hash 
									FROM Profesores 
									WHERE id = (?)""", session["user_id"])

		if not user_hash:
			return "usuario inexistente", 404

		if not check_password_hash(user_hash[0]["hash"], form.pswd.data):
			flash("Contraseña incorrecta", "warning")
			return redirect(url_for(request.endpoint))

		if request.endpoint == "cambiar-usuario":
			q = db_ejecutar("""SELECT usuario 
								FROM Profesores
								WHERE usuario = (?)""",
								form.dato_nuevo.data.strip())
			if q:
				flash("El usuario ya existe", "warning")
				return redirect(url_for(request.endpoint))

			db_ejecutar("""UPDATE Profesores 
							SET usuario = (?)
							WHERE id = (?)""",
							form.dato_nuevo.data.strip(), session["user_id"])

		elif request.endpoint == "cambiar-nombre":
			q = db_ejecutar("""SELECT nombre 
								FROM Profesores
								WHERE nombre = (?)""",
								form.dato_nuevo.data.strip())
			if q:
				flash("El nombre ya existe", "warning")
				return redirect(url_for(request.endpoint))

			db_ejecutar("""UPDATE Profesores 
							SET nombre = (?) 
							WHERE id = (?)""", 
							form.dato_nuevo.data.strip(), session["user_id"])

		elif request.endpoint == "cambiar-pswd":
			pswd_hash = generate_password_hash(form.nueva_pswd.data)
			db_ejecutar("""UPDATE Profesores 
							SET hash = (?) 
							WHERE id = (?)""", pswd_hash, session["user_id"])

		flash("Operación exitosa", "info")
		return redirect(url_for(request.endpoint))

	if request.endpoint != "cambiar-pswd":
		label = f"Nuevo {cat}:" 
		form.dato_nuevo.label.text = label

	endpoint = url_for(request.endpoint)
	return render_template("cambiar_dato.html", form=form, cat=cat, endpoint=endpoint)

@app.route("/reemplazar-profesor", methods=["GET", "POST"])
def reemplazar_prof():

	form = NuevoProfesorForm()

	if form.validate_on_submit():

		clase = form.clase.data.strip()
		profesor = form.nuevo_prof.data.strip()


		clase_id = db_ejecutar("""
						SELECT id
						FROM clases
						WHERE nombre = (?)""", clase)
		
		if not clase_id:
			flash("La clase no existe", "warning")
			return redirect(url_for("reemplazar_prof"))

		clase_id = clase_id[0]["id"] 

		prof_id = db_ejecutar("""SELECT id
									FROM Profesores
									WHERE nombre = (?)""", profesor)
		if not prof_id:
			flash("El profesor no existe", "warning")
			return redirect(url_for("reemplazar_prof"))

		prof_id = prof_id[0]["id"] 

		tiene_profesor = db_ejecutar("""
							SELECT prof_id 
							FROM Clase_Profesor 
							WHERE clase_id = (?)""", clase_id)

		if not tiene_profesor:
			flash("Nigún profesor enseña esta clase", "warning")
			return redirect(url_for("reemplazar_prof"))

		db_ejecutar("""UPDATE Clase_Profesor
						SET prof_id = (?)
						WHERE clase_id = (?)""",
						prof_id, clase_id)

		flash("Operación exitosa", "info")
		return redirect(url_for("reemplazar_prof"))

	return render_template("nuevo_prof.html", form=form)

# pagina registro de profesores/administradores
@app.route("/registrar-profesor", endpoint="r-prof",methods=["GET", "POST"])
@app.route("/registrar-administrador", endpoint="r-admin", methods=["GET", "POST"])
@login_requerido
@admin_requerido
def registrar_profesor():

	form = ProfesorForm()
	if form.validate_on_submit():

		nombre = form.nombre.data.strip()
		usuario = form.usuario.data.strip()
		cat = ""
		admin = 0

		if request.endpoint == "r-prof":
			cat = "profesor"
		elif request.endpoint == "r-admin":
			cat = "administrador"
			admin = 1

		profesores = db_ejecutar("""
			SELECT nombre, usuario 
			FROM Profesores
			WHERE nombre = (?)
			OR usuario = (?)""", nombre, usuario)

		if profesores:
			for prof in profesores:
				if prof["usuario"] == usuario:
					flash("El usuario ya existe", "warning")
				if prof["nombre"] == nombre:
					flash("El nombre ya existe", "warning")

			return redirect(url_for(request.endpoint))

		p_hash = generate_password_hash(form.pswd.data)

		db_ejecutar("""
				INSERT INTO Profesores (nombre, usuario, hash, admin) 
				VALUES (?, ?, ?, ?)""", nombre, usuario, p_hash, admin)

		flash(f"{cat.title()} registrado exitosamente", "info")
		return redirect(url_for(request.endpoint))

	titulo = ""
	cat = ""

	if request.endpoint == "r-prof":
		titulo = "profesores"
		cat = "profesor"
	elif request.endpoint == "r-admin":
		titulo = "administradores"
		cat = "administrador"

	endpoint = url_for(request.endpoint)
	form.submit.label.text = f"Registrar {cat}"

	info = {
		"titulo" : titulo,
		"cat" : cat,
		"endpoint" : endpoint
	}

	return render_template("r_usuario.html", form=form, info=info)
