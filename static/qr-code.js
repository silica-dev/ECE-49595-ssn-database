var qrcode = require("qrcode");

function draw_otp_code(code) {
  var canvas = document.getElementById("qr-code");

  qrcode.toCanvas(canvas, code, function (error) {
    if (error) console.error(error);
    console.log("success!");
  });
}
