from flask import flash
from flask import request
from flask import render_template
from flask import redirect
from flask import session
from flask import url_for

from werkzeug.security import check_password_hash
from asistencias.forms import LoginForm
from asistencias.helpers import *
from asistencias import app

# pagina principal
@app.route("/")
@login_requerido
def index():
	return render_template("index.html")

# pagina login
@app.route("/login", methods=["GET", "POST"])
def login():

	session.clear()

	form = LoginForm()
	if form.validate_on_submit():

		filas = db_ejecutar("""
				SELECT * from Profesores 
				WHERE usuario = (?)""" , form.usuario.data.strip())

		# si el usuario no existe o la contrasena es incorrecta
		if not filas or not check_password_hash(filas[0]["hash"], form.pswd.data):
			flash("Datos incorrectos", "info")
			# por alguna razon flash no funciona con redirect 
			# luego de limpiar la sesion
			return render_template("login.html", form=form)
		
		session["user_id"] = filas[0]["id"]
		session["admin"] = filas[0]["admin"]
		return redirect(url_for("index"))

	return render_template("login.html", form=form)

# cierra la sesion
@app.route("/logout")
def logout():
	session.clear()
	return redirect("/login")