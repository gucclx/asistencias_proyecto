async function extraer_lista(cat, busqueda)
{
	let lista = [];
	try 
	{
		let info = {
			"categoria" : cat,
			"busqueda" : busqueda
		}
		lista = await $.getJSON("/listas", info);
	}
	catch (e)
	{
		console.error(e);
	}
	return lista;
}

function input_valido(categoria, input)
{
	let persona_nombre_regex = /(.*[^a-z ])/i;
	input = input.trim();

	if (input == "") return false;

	if (typeof input === "undefined")
	{
		input = categoria;
		return !persona_nombre_regex.test(input)
	}
	if (categoria != "clase")
	{
		return !persona_nombre_regex.test(input)
	}
	return true
}

// devuelve la fecha y tiempo
// en formato yyyy-mm-dd, hh:mm:ss

// https://stackoverflow.com/a/3067896
function datetime(unixtime)
{
	let date_obj = new Date(unixtime)
	let mm = date_obj.getMonth() + 1; // getMonth() is zero-based
  	let dd = date_obj.getDate();

  	let date = [date_obj.getFullYear(),
		          (mm>9 ? "" : '0') + mm,
		          (dd>9 ? "" : '0') + dd
		         ].join("-");

	let time = date_obj.toTimeString().split(" ")[0]

	return [date, time]
}

// https://stackoverflow.com/a/6234804
function escapeHtml(unsafe) {
    return unsafe
         .replace(/&/g, "&amp;")
         .replace(/</g, "&lt;")
         .replace(/>/g, "&gt;")
         .replace(/"/g, "&quot;")
         .replace(/'/g, "&#039;");
 }

function config_caja_resultados(categoria, res_box_id, _input_id, target_id)
{
    if (!target_id)
    {
        target_id = _input_id;
    }

    let caja = new ResultsBox();
    caja.target_id = target_id;
    caja.res_box_id = res_box_id;
    caja.input_id = _input_id;

    $(_input_id).off();
    $(_input_id).on("keyup", async e => {
        let busqueda = e.target.value;
        if (!input_valido(categoria, busqueda))
        {
            $(res_box_id).fadeOut("fast");
            return;
        } 
        caja.spinner();
        let resultados = await extraer_lista(categoria, busqueda);
        caja.results = resultados;
        caja.show_results();
    });
	$(document).click(e=> {
		$(caja.res_box_id).fadeOut("fast");
	});
	$(caja.res_box_id).click(e=> {
		e.stopPropagation();
	});
    return caja;
}

function enviar_form(info)
{
	if (!info.url || !info.form || !info.csrf) 
	{
		console.error("Faltan datos.");
		return;
	}
    let data = info.form;
    data += info.extra_data || "";

    $.ajax({
        type: "POST",
        url: info.url,
        data: data,
        success: url => {
        	window.location.href = url;
        },
        error: res => {
        	console.error(res);
        }

    });
	$.ajaxSetup({
	    beforeSend: function(xhr, settings) {
	        if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) 
	            && !this.crossDomain) {
	            xhr.setRequestHeader("X-CSRFToken", info.csrf)
	        }
	    }
	});
}