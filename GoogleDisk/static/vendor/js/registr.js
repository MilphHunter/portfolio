// Focus Registration
$(function () {
    $('.form-holder').delegate("input", "focus", function () {
        $('.form-holder').removeClass("active");
        $(this).parent().addClass("active");
    })
})

function formatPinCode(input) {
    var pin = input.value.replace(/\D/, "");
    pin = pin.match(/.{1,1}/g);
    if (pin) {
        input.value = pin.join("-");
    }
}