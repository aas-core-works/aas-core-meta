console.log("oi!");
var activeElement = document.querySelector("#menu .active");
if (activeElement) {
  var rect = activeElement.getBoundingClientRect();
  var menu = document.getElementById("menu");
  var fontSize = parseFloat(getComputedStyle(menu).fontSize);
  // Go two lines up so that the reader immediately sees that there are more options.
  menu.scrollTop = rect.top - 2 * fontSize;
}
