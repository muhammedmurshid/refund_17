/** @odoo-module **/
import { registry } from "@web/core/registry";
import publicWidget from "@web/legacy/js/public/public_widget";

$(document).ready(function() {
    console.log('hiiiiiii')
    $('#amount_one').on('change', function() {
            console.log('kok');
            var value1 = parseFloat($('#amount_one').val());
            var value2 = parseFloat($('#amount_two').val());
            var value3 = parseFloat($('#amount_three').val());

            var total = (isNaN(value1) ? 0 : value1) + (isNaN(value2) ? 0 : value2) + (isNaN(value3) ? 0 : value3);

            $('#amount_total').val(total.toFixed(2));
        });
        $('#amount_two').on('change', function() {
            console.log('kok');
            var value1 = parseFloat($('#amount_one').val());
            var value2 = parseFloat($('#amount_two').val());
            var value3 = parseFloat($('#amount_three').val());

            var total = (isNaN(value1) ? 0 : value1) + (isNaN(value2) ? 0 : value2) + (isNaN(value3) ? 0 : value3);

            $('#amount_total').val(total.toFixed(2));
        });
        $('#amount_three').on('change', function() {
            console.log('kok');
            var value1 = parseFloat($('#amount_one').val());
            var value2 = parseFloat($('#amount_two').val());
            var value3 = parseFloat($('#amount_three').val());

            var total = (isNaN(value1) ? 0 : value1) + (isNaN(value2) ? 0 : value2) + (isNaN(value3) ? 0 : value3);

            $('#amount_total').val(total.toFixed(2));
        });
//        document.getElementById("submit").style.display = "none";
//        document.getElementById("vehicle1").addEventListener("click", function() {
//        var isAgreed = this.checked;
//        if (!isAgreed) {
//        document.getElementById("submit").style.display = "none";
//        console.log('kkk');
//        } else {
//            document.getElementById("submit").style.display = "block";
//        }
//        });


});

