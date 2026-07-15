
// For locatoion 
async function getShopGPS() {
    const statusEl = document.getElementById("locationStatus");
    const addressInput = document.getElementById("id_address");
    const latInput = document.getElementById("id_latitude");
    const lngInput = document.getElementById("id_longitude");

    if (!navigator.geolocation) {
        alert("Your browser does not support GPS.");
        return;
    }

    statusEl.textContent = "Detecting your location...";
    addressInput.value = "";

    navigator.geolocation.getCurrentPosition(
        async function (position) {
            let lat = position.coords.latitude;
            let lng = position.coords.longitude;

            latInput.value = lat;
            lngInput.value = lng;

            try {
                const response = await fetch(
                    `https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=${encodeURIComponent(lat)}&lon=${encodeURIComponent(lng)}&addressdetails=1`,
                    {
                        headers: {
                            Accept: "application/json",
                        },
                    },
                );

                if (!response.ok) {
                    throw new Error("Reverse geocoding failed");
                }

                const data = await response.json();
                const address = data.display_name || "";
                addressInput.value = address;
                statusEl.textContent = address
                    ? "Address auto-filled successfully."
                    : "Location detected, but address lookup returned no address.";
            } catch (error) {
                console.error(error);
                statusEl.textContent =
                    "Coordinates detected, but address lookup failed. Please try again.";
            }
        },
        function (error) {
            statusEl.textContent =
                "Unable to detect location. Please enable location services in your browser.";
        },
        {
            enableHighAccuracy: true,
            timeout: 15000,
            maximumAge: 0,
        },
    );
}

// For second Navbar
document.addEventListener('DOMContentLoaded', function () {
  // Show the secondary navigation on scroll-up and hide it on scroll-down.
    const secondaryNavbar = document.getElementById("secondaryNavbar");
    if (secondaryNavbar) {
        let previousScrollY = window.scrollY;

        window.addEventListener("scroll", () => {
            const currentScrollY = window.scrollY;

            // Only apply this behavior on mobile screens
            if (!window.matchMedia("(max-width: 576px)").matches) {
                secondaryNavbar.classList.remove("navbar-hidden");
                return; // Exit if not on mobile
            }

            // Always show navbar at the top of the page
            if (currentScrollY < 10) {
                secondaryNavbar.classList.remove("navbar-hidden");
            } else if (currentScrollY < previousScrollY) {
                // Scrolling up -> Show
                secondaryNavbar.classList.remove("navbar-hidden");
            } else if (currentScrollY > previousScrollY) {
                // Scrolling down -> Hide
                secondaryNavbar.classList.add("navbar-hidden");
            }

            previousScrollY = currentScrollY;
        }, { passive: true });
    }
});