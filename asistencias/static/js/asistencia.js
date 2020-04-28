let asistencia = []

$("#clases_select").select2({width: "100%"});

$("#clases_select").on("change", e => {
	let clase_id = $("#clases_select").val();
	if (clase_id <= 0)
	{
		$("#asistencia_contenedor").fadeOut("fast");
		$("#ningun_alumno").fadeOut("fast");
		$("#scroll_btn").fadeOut("fast");
		return;
	}
	$("#spinner").fadeIn("fast");
	cargar_alumnos(clase_id);
	setTimeout(() => {
		$("#carnet_input").focus();
	}, 0);
});

async function cargar_alumnos(clase_id)
{

	try
	{
		asistencia = await $.getJSON(
					"listas-asistencia-hoy", 
					{"clase_id" : clase_id});
	}
	catch (e)
	{
		console.error(e);
		return;
	}

	let html = [];

	for (let alumno of asistencia)
	{
		let nombre = escapeHtml(alumno.nombre);
		let carnet = escapeHtml(alumno.carnet);

		let estado, td_class = "";
		let fecha = alumno.fecha;
		let tiempo = alumno.tiempo;

		if (alumno.presente)
		{
			estado = "Presente";
			td_class = "table-success";
		}
		else
		{
			estado = "Ausente";
			td_class = "table-danger";
			tiempo = "";
		}

		let btn_text = alumno.presente == 1 ? "Ausente" : "Presente";

		html.push(`
			<tr data-carnet="${carnet}">
				<td>${nombre}</td>
				<td>${carnet}</td>
				<td class="${td_class}">${estado}</td>
				<td>${fecha}</td>
				<td>${tiempo}</td>
				<td>
					<button class="marcar-alumno btn btn-primary">
						${btn_text}
					</button>
				</td>
			</tr>`);
	}

	if (html.length == 0)
	{
		$("#asistencia_contenedor").hide();
		$("#ningun_alumno").fadeIn("fast");
		return;
	}

	$("#asistencia_tbody").html(html.join(""));
	$("#ningun_alumno").hide();
	$("#spinner").hide();
	$("#asistencia_contenedor").fadeIn("fast");
	$("#scroll_btn").fadeIn("fast");
}

$(document).on("click", "button.marcar-alumno", e => {

	let btn = e.target;

	let tabla_fila = $(btn).parents("tr");

	let td_estado = $(tabla_fila).children().eq(2);
	let td_fecha  = $(tabla_fila).children().eq(3);
	let td_tiempo = $(tabla_fila).children().eq(4);

	let carnet = $(tabla_fila).data("carnet");

	for (let alumno of asistencia)
	{
		if (alumno.carnet != carnet) continue;

		marcar_alumno(alumno, invertir=true);
		let nombre = escapeHtml(alumno.nombre);

		let estado, td_class = "";
		let fecha, tiempo = "";
		let btn_html = "";

		if (alumno.presente)
		{
			estado = "Presente";
			td_class = "table-success";
			$(btn).html("Ausente");
		}
		else
		{
			estado = "Ausente";
			td_class = "table-danger";
			$(btn).html("Presente");
		}

		fecha = alumno.fecha;
		tiempo = alumno.tiempo;

		if (!alumno.presente) tiempo = "";

		$(td_estado).html(estado);
		$(td_estado).attr("class", td_class);

		$(td_fecha).html(fecha);
		$(td_tiempo).html(tiempo);

		break;
	}
});

// marca al alumno como presente
// si invertir es falso
function marcar_alumno(alumno, invertir=false)
{
	let hoy = new Date();

	// string en formato yyyy-mm-dd HH:MM:SS
	let fecha, tiempo;

	[fecha, tiempo] = datetime(hoy.getTime());

	if (!invertir && alumno.presente == 0)
	{
		alumno.presente = 1;
		alumno.fecha = fecha;
		alumno.tiempo = tiempo;
	}
	else
	{
		alumno.presente = alumno.presente == 1 ? 0 : 1;

		if (alumno.presente)
		{
			alumno.fecha = fecha;
			alumno.tiempo = tiempo;
			return;
		}

		hoy.setHours(0);
		hoy.setMinutes(0);
		hoy.setSeconds(0);

		alumno.fecha = fecha;
	}
}

$("#carnet_input").on("keydown", e => {

	let enter = e.keyCode == 13 || e.which == 13;

	if (!enter) return;

	e.preventDefault();

	let carnet = $("#carnet_input").val().trim();
	let tabla_fila = $(`[data-carnet=${carnet}]`);

	for (let alumno of asistencia)
	{
		if (alumno.carnet != carnet) continue;
		if (alumno.presente) break;

		marcar_alumno(alumno);

		let nombre = escapeHtml(alumno.nombre);

		let fecha = alumno.fecha;
		let tiempo = alumno.tiempo;

		$(tabla_fila).html(`
			<td>${nombre}</td>
			<td>${carnet}</td>
			<td class="table-success">Presente</td>
			<td>${fecha}</td>
			<td>${tiempo}</td>
			<td>
				<button class="marcar-alumno btn btn-primary">
					Ausente
				</button>
			</td>`);

		break;
	}

	$("#carnet_input").val("");
	$("#carnet_input").focus();
});

$("#submit_btn").on("click", e => {
	e.preventDefault();

	let extra_data = `&alumnos=${JSON.stringify(asistencia)}`;
	let form = "#asistencia_form";

	let info = {
		form : $(form).serialize(),
		url : $(form).prop("action"),
		csrf : $("#csrf_token").val(),
		extra_data : extra_data
	};
	enviar_form(info);
});
