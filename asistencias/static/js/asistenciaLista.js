let ASISTENCIA = (function() {

    $("#clases_select").select2({width: "100%"});

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

    $(document).on("change", "input[type=radio]", e => {
        let radio = $(e.target).data("periodo");
        if (radio == "rango")
        {
            $("#evaluar_btn").html("Ver rangos");
            return;
        }
        $("#evaluar_btn").html("Generar lista");
    });

    $(document).on({
        ajaxStart: () => {
            mostrar_segmento("#spinner");
        },
        ajaxStop: () => {
            $("#spinner").hide();
        } 
    });

    function mostrar_segmento(segmento)
    {
        let segs = ["#inicio", "#opciones_rango", 
                    "#asistencia_div", "#ningun_resultado", "#spinner"];

        for (let seg of segs)
        {
            if (seg == segmento)
            {
                if (seg == "#asistencia_div" || seg == "#spinner")
                {
                    $(".navbar").hide();
                }
                else
                {
                    $(".navbar").show();
                }
                $(seg).fadeIn("fast");
                mostrar_botones(seg);
                continue;
            }
            $(seg).hide();
        }
    }

    // muestra los botones correspondientes para cada segmento
    function mostrar_botones(segmento)
    {
        let seg_botones = {}

        seg_botones["#asistencia_div"] = ["#volver_btn", "#excel_btn", "#scroll_btn"]
        seg_botones["#opciones_rango"] = ["#rangos_btn", "#volver_btn"]
        seg_botones["#ningun_resultado"] = ["#volver_btn"]

        seg_botones["#spinner"] = []
        seg_botones["#inicio"]  = ["#evaluar_btn"]

        let botones = ["#volver_btn", "#excel_btn", "#rangos_btn", 
                        "#evaluar_btn", "#scroll_btn"];

        for (let btn of botones)
        {
            if (seg_botones[segmento].includes(btn))
            {
                if (btn == "#scroll_btn")
                {
                    document.documentElement.scrollTo(0, 0);
                    $("#scroll_icon").html("arrow_downward");
                    $(btn).data("target", "bottom");
                }
                $(btn).fadeIn("fast");
                continue;
            }
            $(btn).hide();
        }
    }

    // asigna el segmento anterior y actual al boton "volver".
    // tambien devuelve tales segmentos si set == false
    function volver_btn_config(set=false, prev="", curr="")
    {
        if (set == true)
        {
            $("#volver_btn").data("prev", prev);
            $("#volver_btn").data("curr", curr);
            return;
        }
        prev = $("#volver_btn").data("prev");
        curr = $("#volver_btn").data("curr");
        return [prev, curr]
    }

    function cargar_asistencia(info)
    {

        let settings = {
            url : "/listas-asistencia",
            data : JSON.stringify(info),
            contentType : "application/json",
            dataType : "json"
        }

        $.post(settings).done(asistencia => {
            
            let html = [];

            for (let alumno of asistencia)
            {
                let nombre = escapeHtml(alumno.nombre);
                let carnet = escapeHtml(alumno.carnet);

                let estado;
                let td_class;
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
                    // omitir tiempo
                    tiempo = "";
                }

                html.push(
                    `<tr>
                        <td>${nombre}</td>
                        <td>${carnet}</td>
                        <td class="${td_class}">${estado}</td>
                        <td>${fecha}</td>
                        <td>${tiempo}</td>
                    </tr>`);
            }

            if (html.length == 0)
            {
                mostrar_segmento("#ningun_resultado");
                return;
            }
            $("#asistencia_tbody").html(html.join(""))
            $("#excel_btn").off();
            $("#excel_btn").on("click", e => {
                generar_excel(asistencia);
            });
            mostrar_segmento("#asistencia_div");

        }).fail(res => {
            console.error(res);
            mostrar_segmento("#inicio");
        });
    }

    // envia la asistencia a la ruta /exportar-excel
    // para generar un excel de esta
    function generar_excel(asistencia)
    {
        if (!asistencia) return;
        let xhttp = new XMLHttpRequest();
        xhttp.onload = () => {

            if (xhttp.status == 200 && xhttp.readyState == 4)
            {
                /* descargar Excel */
                
                let a = document.createElement("a");
                a.href = URL.createObjectURL(xhttp.response);
                a.style.display = "none";
                clase_nombre = $("#clases_select option:selected").html().trim();
                archivo_nombre = clase_nombre;
                let tiempo_actual = new Date().getTime();
                let yy_mm_dd = datetime(tiempo_actual)[0];
                archivo_nombre += `-reporte(${yy_mm_dd}).xlsx`;

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
            mostrar_segmento("#inicio");
        }
        xhttp.open("POST", "/exportar-excel-json");
        xhttp.responseType = "blob";
        xhttp.setRequestHeader("Content-Type", "application/json");
        xhttp.send(JSON.stringify(asistencia));
        mostrar_segmento("#spinner");
    }

    return {

        volver: function ()
        {
            // segmento anterior y actual
            let anterior, actual;

            [anterior, actual] = volver_btn_config();

            mostrar_segmento(anterior);

             if (actual == "#asistencia_div") {
                volver_btn_config(true, "#inicio");
            }
        },

        asistencia_rangos : function ()
        {
            // fechas de los calendarios
            let f1 = $("#fecha_inicial").val();
            let f2 = $("#fecha_final").val();

            // evalular que sean strings validas
            if (isNaN(new Date(f1).getTime())) return;
            if (isNaN(new Date(f2).getTime())) return;

            let clase_id = $("#clases_select").val();

            if (!clase_id) return;

            let info = {
                "usar_rango" : true,
                "fecha_inicial" : f1,
                "fecha_final" : f2,
                "clase_id" : clase_id
            }
            cargar_asistencia(info, clase_id);
            volver_btn_config(true, "#opciones_rango", "#asistencia_div");
        },

        // evalua cual radio btn esta seleccionado 
        evaluar_radios : function ()
        {
            let periodo = $("input[type=radio]:checked").data("periodo");
            if (!periodo) return;

            let clase_id = $("#clases_select").val();

            if (!clase_id) return;

            if (periodo != "rango")
            {
                let info = {
                    "usar_rango" : false,
                    "periodo" : periodo,
                    "clase_id" : clase_id
                }
                cargar_asistencia(info);
                volver_btn_config(true, "#inicio", "#asistencia_div");
            }
            else
            {
                mostrar_segmento("#opciones_rango");
                volver_btn_config(true, "#inicio", "#asistencia_div");
            }
        }
    }

}());

$("#evaluar_btn").click(() => {
    ASISTENCIA.evaluar_radios();
});
$("#rangos_btn").click(() => {
    ASISTENCIA.asistencia_rangos();
});
$("#volver_btn").click(() => {
    ASISTENCIA.volver();
});