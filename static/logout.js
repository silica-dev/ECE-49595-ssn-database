function logout() {
  const xhr = new XMLHttpRequest();
  xhr.open("POST", "/logout", true);
  csrf_token = document.cookie
    .split(";")
    .find((row) => row.startsWith("csrf_access_token="))
    ?.split("=")[1];
  xhr.setRequestHeader("X-CSRF-TOKEN", `${csrf_token}`);

  xhr.onreadystatechange = () => {
    if (xhr.readyState === xhr.DONE) {
      document.location.reload();
    }
  };
  xhr.send(null);
}
