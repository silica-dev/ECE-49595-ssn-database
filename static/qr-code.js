var qrcode = require("qrcode");

function draw_otp_code() {
  var canvas = document.getElementById("canvas");

  qrcode.toCanvas(canvas, "OTP QR Code", function (error) {
    if (error) console.error(error);
    console.log("success!");
  });
}
