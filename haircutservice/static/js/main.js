
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

// <!-- signup form  -->
const form = document.getElementById("signupForm");

form.addEventListener("submit", function (e) {

    const phone = document.getElementById("phonenumber").value;
    const errorBox = document.getElementById("jsPasswordError");

    if (!/^\d{10}$/.test(phone)) {
        e.preventDefault(); // Form submit hone se rok dega

        errorBox.classList.remove("d-none");
        errorBox.innerText = "Mobile number must be exactly 10 digits.";
        return;
    }

    errorBox.classList.add("d-none");
});