document.querySelector("form").addEventListener("formdata", (event) => {
  csrf_token = document.cookie
    .split(";")
    .find((row) => row.startsWith("csrf_access_token="))
    ?.split("=")[1];
  formData = event.formData;

  formData.append("csrf_token", csrf_token);
});
