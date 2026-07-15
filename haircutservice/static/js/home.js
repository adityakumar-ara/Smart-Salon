document.addEventListener("DOMContentLoaded", function () {
    // Horizontal scroll on slider with mouse wheel
    const slider = document.querySelector('.custom-slider');

    if (slider) {
        slider.addEventListener('wheel', (evt) => {
            evt.preventDefault();
            slider.scrollLeft += evt.deltaY * 1.2;
        }, { passive: false });
    }

    // Show login prompt on profile mouseover for guests
    const profiles = document.querySelectorAll('.static-profile');
    profiles.forEach(function (profile) {
        profile.addEventListener("mouseover", function () {
            // Prevent multiple alert boxes from appearing.
            if (document.querySelector('.alert_box')) {
                return;
            }
            const alertBox = document.createElement("div");
            alertBox.className = "alert_box";
            alertBox.textContent = "First of all Login Please";

            document.body.appendChild(alertBox);

            setTimeout(() => {
                alertBox.remove();
            }, 2000);
        });
    });
});