/* implementa la funcionalidad del boton desplazamiento */

$(function (){
    $("#scroll_btn").click(() => {

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
        document.documentElement.scrollTo(0, scrollTop);
    });

    $(document).on("scroll", e => {

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