let caja_clases = config_caja_resultados("clase", "#clase_resultados", 
											"#clase_input", "#tags");

let calendarios = ["#f1", "#f2"];
let calendarios_inputs = ["#fecha_inicial", "#fecha_final"];

// configurar calendarios
for (let i = 0; i < calendarios.length; i++)
{
	$(calendarios[i]).datepicker({
		dateFormat : "yy-mm-dd",
		altField: calendarios_inputs[i]
	});
}

$("#continuar_btn").click(() => {
	if (caja_clases.tags.length <= 0)
	{
		return;
	}
	mostrar_segmento("#opciones");
	$("#volver_btn").data("prev", "#inicio");
});

$(".exportar-btn").click(e => {

	let periodo = $(e.target).data("periodo");
	let clases  = caja_clases.tags;

	if (periodo != "rango")
	{
		let info = {
			"usar_rango" : false,
			"periodo" : periodo,
			"clases" : clases
		}
		enviar_info("/exportar-excel", info);
		return;
	}

	let f1 = $("#fecha_inicial").val();
	let f2 = $("#fecha_final").val();

	// verificar que el usuario provea fechas
	if (!f1 || !f2) return;

	// evalular que sean strings validas
	if (isNaN(new Date(f1).getTime())) return;
	if (isNaN(new Date(f2).getTime())) return;

	let info = {
		"usar_rango" : true,
		"fecha_inicial" : f1,
		"fecha_final" : f2,
		"clases" : clases
	}
	enviar_info("/exportar-excel", info);
});

$("#volver_btn").click(() => {
	let anterior = $("#volver_btn").data("prev");
	let actual   = $("#volver_btn").data("curr");

	mostrar_segmento(anterior);

	if (actual == "#fecha_rangos")
	{
		$("#volver_btn").data("prev", "#inicio");
	}
});

$("#mostrar_rangos_btn").click(() => {
	mostrar_segmento("#fecha_rangos");
	$("#volver_btn").data("prev", "#opciones");
	$("#volver_btn").data("curr", "#fecha_rangos");
});


function enviar_info(url, info)
{
    let xhttp = new XMLHttpRequest();
    xhttp.onload = () => {

        if (xhttp.status == 200 && xhttp.readyState == 4)
        {
        	/* descargar el zip */

            let a = document.createElement("a");
            a.href = URL.createObjectURL(xhttp.response);
            a.style.display = "none";

            let tiempo_actual = new Date().getTime();
            let yy_mm_dd = datetime(tiempo_actual)[0];
            let archivo_nombre = `Asistencia(${yy_mm_dd}).zip`;

            a.download = archivo_nombre;
            document.body.appendChild(a);
            a.click();
            URL.revokeObjectURL(a.href);
        }

        if (xhttp.status != 200 && xhttp.readyState == 4)
        {
            let reader = new FileReader();
            reader.addEventListener("loadend", e => {
                let res = e.srcElement.result;
                console.error(res);
            });
            reader.readAsText(xhttp.response);
        }
        caja_clases.clear();
        mostrar_segmento("#inicio");
    }
    xhttp.open("POST", url);
    xhttp.responseType = "blob";
    xhttp.setRequestHeader("Content-Type", "application/json");
    xhttp.send(JSON.stringify(info));
    mostrar_segmento("#spinner");
}

function mostrar_segmento(segmento)
{
	let segs = ["#inicio", "#opciones", "#fecha_rangos", "#spinner"];

	for (let seg of segs)
	{
		if (seg == segmento)
		{
			$(seg).fadeIn("fast");
			mostrar_botones(seg);
			continue;
		}
		$(seg).hide();
	}
}

function mostrar_botones(segmento)
{
	let segs = {};
	segs["#inicio"] = ["#continuar_btn"];
	segs["#opciones"] = ["#volver_btn"];
	segs["#fecha_rangos"] = ["#volver_btn", "#rangos_btn"];
	segs["#spinner"] = [];

	let btns = ["#continuar_btn", "#volver_btn", "#rangos_btn"];

	for (let btn of btns)
	{
		if (segs[segmento].includes(btn))
		{
			$(btn).show();
			continue;
		}
		$(btn).hide();
	}
}