function snackbarShow(message, bootstrap_colour) {
    console.log("show bg-"+bootstrap_colour)
    // Get the snackbar DIV
    var x = document.getElementById("snackbar");
    x.innerHTML = message;
    // Add the "show" class to DIV
    x.className = "show bg-"+bootstrap_colour;
    // After 3 seconds, remove the show class from DIV
    setTimeout(function() { x.className = x.className.replace("show", ""); }, 3000);
}