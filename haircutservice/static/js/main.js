// const profile = document.querySelector(".static-profile");

// profile.addEventListener("mouseover", function () {
//     document.querySelector('.alert').innerHTML="Plz SingUp and Login ";
// });


document.addEventListener("DOMContentLoaded", function () {
    const profiles = document.querySelectorAll('.static-profile, .profile');
    if (!profiles || profiles.length === 0) return;

    profiles.forEach(function (profile) {
        profile.addEventListener("mouseover", function () {
            const alertBox = document.createElement("div");
            alertBox.className = "alert_box";
            alertBox.textContent = " First of all Login Please";

            document.body.appendChild(alertBox);

            setTimeout(() => {
                alertBox.remove();
            }, 2000);
        });
    });
});