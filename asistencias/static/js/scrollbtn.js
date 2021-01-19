/* implementa la funcionalidad del boton desplazamiento */

$(function (){
    $("#scroll_btn").click(() => {

        // invertir direccion
        let scrollTop;
        let target = $("#scroll_btn").data("target");
        switch (target)
        {
            case "top" :
                scrollTop = 0;
                $("#scroll_icon").html("arrow_downward");
                $("#scroll_btn").data("target", "bottom");       
            break;

            case "bottom" : 
                scrollTop  = $("html, body").height();
                $("#scroll_icon").html("arrow_upward");
                $("#scroll_btn").data("target", "top");
            break;
        }
        // desplazar hacia la direccion
        document.documentElement.scrollTo(0, scrollTop);
    });

    $(document).on("scroll", e => {

        // calcular direccion cuando el usuario se desplace por la pagina

        let scrolled = document.body.scrollTop || document.documentElement.scrollTop;

        let scrollHeight = document.documentElement.scrollHeight;
        let clientHeight = document.documentElement.clientHeight;

        let midpoint = (scrollHeight - clientHeight) / 2;

        if (scrolled > midpoint)
        {
            $("#scroll_icon").html("arrow_upward");
            $("#scroll_btn").data("target", "top");
        }
        else if (scrolled < midpoint)
        {
            $("#scroll_icon").html("arrow_downward");
            $("#scroll_btn").data("target", "bottom");
        }
    });
});