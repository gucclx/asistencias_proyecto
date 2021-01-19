from flask_wtf import FlaskForm
from wtforms import BooleanField
from wtforms import PasswordField
from wtforms import StringField
from wtforms import SubmitField
from wtforms import SelectField
from wtforms import SelectMultipleField
from wtforms.validators import DataRequired
from wtforms.validators import EqualTo
from wtforms.validators import Length
from wtforms.validators import Regexp

nombre_invalido_persona = "Solo se permiten letras y espacios"
persona_nombre_regex = "^[a-zA-Z ]+$"

min_len = 3
max_len = 255

len_regex = "(.*[^ ]){3,255}"
len_invalida = f"""Mínimo de caracteres {min_len}, máximo {max_len}"""

carnet_regex = "^[ ]*[a-zA-Z0-9]+$"
carnet_invalido = "Solo se permiten letras y números"

usuario_regex = "^[ ]*[a-zA-Z0-9-_]*[ ]*$"
usuario_invalido = "Solo se permiten letras, numeros, guiones y guiones bajos"

pswd_regex = "(.*[^ ]){6,}"
pswd_invalida = "Al menos 6 caracteres y sin espacios"


class AlumnoForm(FlaskForm):

	nombre = StringField("Nombre:",validators=[DataRequired(), 
												Regexp(persona_nombre_regex, message=nombre_invalido_persona),
												Regexp(len_regex, message=len_invalida)])

	carnet = StringField("Carnet:", 
						validators=[DataRequired(), 
									Regexp(carnet_regex, message=carnet_invalido),
									Regexp(len_regex, message=len_invalida)])
	
	clases_field = StringField("Clases del alumno (opcional):")
	submit = SubmitField("Registrar alumno")


class ClaseForm(FlaskForm):

	nombre = StringField("Nombre:", validators=[DataRequired(),
												Regexp(len_regex, message=len_invalida)])

	profesor = StringField("Profesor de la clase (opcional):")

	submit = SubmitField("Registrar clase")

class ProfesorForm(FlaskForm):

	nombre  = StringField("Nombre:", 
						validators=[DataRequired(), 
						Regexp(persona_nombre_regex, message=nombre_invalido_persona),
						Regexp(len_regex, message=len_invalida)])
	usuario = StringField("Usuario:", 
						validators=[Regexp(usuario_regex, message=usuario_invalido),
						Regexp(len_regex, message=len_invalida)])

	pswd = PasswordField("Contraseña:", validators=[DataRequired(), Regexp(pswd_regex, message=pswd_invalida)])
	pswd_confirmar = PasswordField("Confirmar contraseña:", 
								validators=[EqualTo("pswd", message="Las contraseñas no coinciden")])
	submit = SubmitField()

class EliminarEntradaForm(FlaskForm):

	categoria = SelectField("Seleccionar categoria:", choices=[("alumno", "Alumno"), 
																("profesor", "Profesor"), 
																("clase", "Clase")])

	nombre = StringField("Nombre del alumno:", validators=[DataRequired()])
	submit = SubmitField("Confirmar")

class LoginForm(FlaskForm):

	usuario = StringField("Usuario:", validators=[DataRequired()])
	pswd    = PasswordField("Contraseña:", validators=[DataRequired()])
	submit  = SubmitField("Acceder")

class AsistenciaForm(FlaskForm):

	clases = SelectField("Clase:", choices=[(-1, "Seleccionar")], coerce=int)
	carnet = StringField("Carnet:")
	submit = SubmitField("Guardar asistencia")
	
class ClasePersonaForm(FlaskForm):

	persona = StringField(validators=[DataRequired()])
	clase   = StringField()
	submit  = SubmitField("Confirmar")

class CambiarDatosForm(FlaskForm):

	dato_nuevo = StringField()
	pswd = PasswordField("Contraseña:", validators=[DataRequired()])
	submit = SubmitField("Confirmar")

class CambiarPswdForm(FlaskForm):

	pswd  = PasswordField("Actual:", validators=[DataRequired()])
	nueva_pswd = PasswordField("Nueva:", validators=[DataRequired(), 
												Regexp(pswd_regex, message=pswd_invalida)])

	repetir = PasswordField("Repetir:", validators=[DataRequired(),
													EqualTo("nueva_pswd", message="Las contraseñas no coinciden")])
	submit  = SubmitField("Confirmar")

class NuevoProfesorForm(FlaskForm):

	clase = StringField("Clase:", validators=[DataRequired()])
	nuevo_prof = StringField("Nuevo profesor de la clase:", validators=[DataRequired()])
	submit = SubmitField("Reemplazar")

class NuevoNombreClase(FlaskForm):

	clase = StringField("Clase:", validators=[DataRequired()])
	nombre = StringField("Nuevo nombre:", validators=[DataRequired()])
	
	submit = SubmitField("Confirmar")