// adapted from zxcvbn-ts documentation

function initialize_checker() {
  const options = {
    translations: zxcvbnts["language-en"].translations,
    graphs: zxcvbnts["language-common"].adjacencyGraphs,
    dictionary: {
      ...zxcvbnts["language-common"].dictionary,
      ...zxcvbnts["language-en"].dictionary,
    },
  };

  zxcvbnts.core.zxcvbnOptions.setOptions(options);
}

function update_check() {
  let passwd = document.getElementById("password").value;
  let res = zxcvbnts.core.zxcvbn(passwd);
  let ratio = res.score / 4;

  // update bar
  let bar = document.getElementById("passwd-strength");
  bar.style.flex = ratio;
}

function validate_account_info() {
  let info = document.forms["register"];
  if (
    info["password"].value.length < 8 ||
    info["password"].value.length > 128
  ) {
    alert("password is not the correct size");
    return false;
  }
  if (info["ssn"].value.length != 9) {
    alert("invalid social security number");
    return false;
  }
}
