 /* implementa la funcionalidad de la caja de resultados */
/* 
res_box_id : id del div donde se colocan los resultados.
target_id : id del elemento (div o input) donde se coloca 
el resultado una vez se da click en el.
input_id : id del input donde el usuario escribe
results : lista de resultados que apareceran en la caja.
tags : si el target_id es un div, los resultados seran
agregados con apariencia de 'tags', esta variable se encarga de mantener
la informacion de cada uno (nombre, id/carnet del resultado). */

class ResultsBox
{
	constructor()
	{
		this.res_box_id = "";
		this.target_id = "";
		this.input_id = "";
		this.results = [];
		this.tags  = [];
	}

	show_results()
	{
		$(this.res_box_id).html("");
		if (this.results.length == 0)
		{
			let div = document.createElement("div");
			div.textContent = "Ningún resultado";
			$(this.res_box_id).append(div);
			$(this.res_box_id).fadeIn("fast");
			return;
		}
		for (let res of this.results)
		{
			let div = document.createElement("div");
			div.setAttribute("data-targetid", this.target_id);
			div.setAttribute("data-id", res.id || res.carnet);
			div.addEventListener("click", e => this.add_result(e.target));
			div.textContent = res.nombre;
			$(this.res_box_id).append(div);
		}
		$(this.res_box_id).fadeIn("fast");
	}

	add_result(res)
	{
		let target_type = $(this.target_id).prop("nodeName").toLowerCase();

		if (target_type == "input")
		{
			$(this.target_id).val(res.textContent);
			$(this.res_box_id).hide();
			return;
		}

		let res_id = $(res).data("id");
		for (let i = 0; i < this.tags.length; i++)
		{
			if (res_id != this.tags[i].id) continue;
			$(this.input_id).val("");
			$(this.res_box_id).hide();
			return;
		}
		this.tags.push({nombre : res.textContent, id : res_id});

		let div  = document.createElement("div");
		let span = document.createElement("span");
		let close_button = document.createElement("button");

		div.setAttribute("class", "tag");
		div.setAttribute("data-tagid", res_id);
		close_button.setAttribute("data-tagid", res_id);
		close_button.setAttribute("class", "pl-1 close");
		close_button.innerHTML = "&times;";
		span.textContent = res.textContent;

		close_button.addEventListener("click", e => {
			e.preventDefault();
			let tag_id = $(e.target).data("tagid");
			$(`[data-tagid="${tag_id}"]`).fadeOut("fast", () => {
				$(`[data-tagid="${tag_id}"]`).remove();
				this.tags = this.tags.filter(tag => tag.id != tag_id);
				if (this.tags.length == 0) $(this.target_id).hide();
			});
		});

		div.appendChild(span);
		div.appendChild(close_button);
		$(this.input_id).val("");
		$(this.input_id).focus();
		$(this.res_box_id).hide();
		$(this.target_id).append(div);
		$(this.target_id).fadeIn("fast");
	}

	clear()
	{
		let type = $(this.target_id).prop("nodeName").toLowerCase();
		if (type != "input")
		{
			$(this.target_id).hide();
		}
		for (let tag of this.tags)
		{
			let tag_id = tag.id;
			$(`[data-tagid="${tag_id}"]`).remove();
		}
		this.tags = [];
		$(this.res_box_id).html("");
	}

	spinner()
	{
		$(this.res_box_id).html(`
			<div>
		        <div class="d-flex justify-content-center">
		            <div class="spinner-border text-primary" role="status">
		                <span class="sr-only">Loading...</span>
		            </div>
		        </div>
		    </div>`)
		$(this.res_box_id).show();
	}
}