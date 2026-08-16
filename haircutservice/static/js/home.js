document.addEventListener("DOMContentLoaded", function () {
    const homeSalonList = document.getElementById("homeSalonList");
    const nearbyStatus = document.getElementById("nearbySalonsStatus");
    let userCoordinates = null;

    if (homeSalonList && nearbyStatus && window.nearbySalonsUrl) {
        filterHomeSalonsByLocation();
    }

    async function filterHomeSalonsByLocation(radiusKm = 5) {
        if (!navigator.geolocation) {
            nearbyStatus.textContent = "Location is not supported by your browser. Showing all salons.";
            return;
        }

        nearbyStatus.textContent = "Finding salons within " + radiusKm + " km of your location...";
        try {
            if (!userCoordinates) {
                const position = await new Promise((resolve, reject) => {
                    navigator.geolocation.getCurrentPosition(resolve, reject, {
                        enableHighAccuracy: true,
                        timeout: 10000,
                        maximumAge: 0,
                    });
                });
                userCoordinates = {
                    latitude: position.coords.latitude,
                    longitude: position.coords.longitude,
                };
            }

            const response = await fetch(
                `${window.nearbySalonsUrl}?lat=${userCoordinates.latitude}&lng=${userCoordinates.longitude}&radius=${radiusKm}`,
            );
            const data = await response.json();
            if (!response.ok || data.error) {
                throw new Error(data.error || "Unable to find nearby salons.");
            }

            const salons = data.salons || [];
            showHomeSalonResults(salons);
            if (salons.length) {
                nearbyStatus.textContent = `${data.total} salon(s) found within ${radiusKm} km of your location.`;
                return;
            }

            if (radiusKm === 5) {
                nearbyStatus.innerHTML = `Aapke 5 km ke andar koi salon registered nahi hai. Kya aap 20 km ke andar salons dekhna chahte hain? <button id="expandSalonSearch" type="button" class="btn btn-sm btn-primary ms-2">Yes, show salons</button>`;
                document.getElementById("expandSalonSearch").addEventListener("click", () => filterHomeSalonsByLocation(20));
            } else {
                nearbyStatus.textContent = "Sorry, aapke 20 km ke andar bhi koi salon registered nahi hai.";
            }
        } catch (error) {
            nearbyStatus.textContent = "Location permission is needed to show salons near you. Showing all salons.";
            showAllHomeSalons();
        }
    }

    function showHomeSalonResults(salons) {
        const nearbyIds = new Set(salons.map((salon) => String(salon.id)));
        homeSalonList.querySelectorAll("[data-salon-id]").forEach((card) => {
            card.classList.toggle("d-none", !nearbyIds.has(card.dataset.salonId));
        });
    }

    function showAllHomeSalons() {
        homeSalonList.querySelectorAll("[data-salon-id]").forEach((card) => card.classList.remove("d-none"));
    }

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
            alertBox.textContent = "Make sure Your are login";

            document.body.appendChild(alertBox);

            setTimeout(() => {
                alertBox.remove();
            }, 2000);
        });
    });
});
