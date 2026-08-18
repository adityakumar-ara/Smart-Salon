
function playCustomerAlert() {
   var sound = document.getElementById("customerSound");
    sound.play().catch(e => console.log("Audio play error:", e));
    document.getElementById("customerActionBox").style.display = "block";
}
