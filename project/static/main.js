$(".toggle-password").click(function () {

    $(this).toggleClass("fa-eye fa-eye-slash");
    var input = $($(this).attr("toggle"));
    if (input.attr("type") == "password") {
        input.attr("type", "text");
    } else {
        input.attr("type", "password");
    }

});

$(function () {
    $('[data-toggle="tooltip"]').tooltip()
})


// to keep navbar fixed


$(function () {
    $(document).scroll(function () {
        var $nav = $(".navbar-fixed-top");
        $nav.toggleClass('scrolled', $(this).scrollTop() > $nav.height());
    });
});



// to get footer year

var currentDate = new Date();
var year = currentDate.getFullYear();
//assigning new year in footer

document.querySelector('#currentYear').textContent = year;