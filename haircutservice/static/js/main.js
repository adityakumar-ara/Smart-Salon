
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

// For active tab highlight
function syncActiveNav() {
    const currentPath = window.location.pathname.replace(/\/+$/, '') || '/';
    const links = document.querySelectorAll('.nav-link, .mobile-secondary-navbar a');

    links.forEach((link) => {
        const href = (link.getAttribute('href') || '').replace(/\/+$/, '') || '/';
        link.classList.remove('active');

        const isHome = currentPath === '/' && href === '/';
        const isMale = currentPath === '/shopkeeper/maleservice' && href === '/shopkeeper/maleservice';
        const isFemale = currentPath === '/shopkeeper/femaleservice' && href === '/shopkeeper/femaleservice';

        if (isHome || isMale || isFemale) {
            link.classList.add('active');
        }
    });
}

// For second Navbar
document.addEventListener('DOMContentLoaded', function () {
  syncActiveNav();

  const secondaryNavbar = document.getElementById("secondaryNavbar");
  if (secondaryNavbar) {
      let previousScrollY = window.scrollY;

      window.addEventListener("scroll", () => {
          const currentScrollY = window.scrollY;

          if (!window.matchMedia("(max-width: 576px)").matches) {
              secondaryNavbar.classList.remove("navbar-hidden");
              return;
          }

          if (currentScrollY < 10) {
              secondaryNavbar.classList.remove("navbar-hidden");
          } else if (currentScrollY < previousScrollY) {
              secondaryNavbar.classList.remove("navbar-hidden");
          } else if (currentScrollY > previousScrollY) {
              secondaryNavbar.classList.add("navbar-hidden");
          }

          previousScrollY = currentScrollY;
      }, { passive: true });
  }

  const toggle = document.getElementById("chatbotToggle");
  const panel = document.getElementById("chatbotPanel");
  const closeBtn = document.getElementById("chatbotClose");
  const form = document.getElementById("chatbotForm");
  const input = document.getElementById("chatbotInput");
  const messages = document.getElementById("chatbotMessages");

  if (toggle && panel) {
      toggle.addEventListener("click", () => {
          panel.classList.toggle("open");
      });
  }

  if (closeBtn && panel) {
      closeBtn.addEventListener("click", () => {
          panel.classList.remove("open");
      });
  }

  document.querySelectorAll(".quick-action").forEach((button) => {
      button.addEventListener("click", () => {
          const text = button.getAttribute("data-message") || button.textContent;
          sendMessage(text);
      });
  });

  if (form && input && messages) {
      form.addEventListener("submit", async (event) => {
          event.preventDefault();
          const text = input.value.trim();
          if (!text) return;
          await sendMessage(text);
          input.value = "";
      });
  }

  async function sendMessage(text) {
      const userMessage = document.createElement("div");
      userMessage.className = "message user";
      userMessage.textContent = text;
      messages.appendChild(userMessage);

      const lowerText = text.toLowerCase().trim();
      if (awaitingExpandedSalonSearch && isYesAnswer(lowerText)) {
          awaitingExpandedSalonSearch = false;
          appendBotMessage("Searching for salons within 20 km of your location...");
          await findNearbySalons(20);
          return;
      }

      if (awaitingExpandedSalonSearch && isNoAnswer(lowerText)) {
          awaitingExpandedSalonSearch = false;
          appendBotMessage("No problem. You can search again whenever you want.");
          return;
      }

      if (shouldSearchNearby(text)) {
          awaitingExpandedSalonSearch = false;
          appendBotMessage("Checking salons near your current location...");
          await findNearbySalons(5);
          return;
      }

      const botResponse = document.createElement("div");
      botResponse.className = "message bot";
      botResponse.innerHTML = getBotReply(text);
      messages.appendChild(botResponse);
      messages.scrollTop = messages.scrollHeight;
  }

  function shouldSearchNearby(text) {
      const lower = text.toLowerCase();
      return lower.includes("near") || lower.includes("nearby") || lower.includes("around me") || lower.includes("closest") || lower.includes("my near salon") || lower.includes("nearest salon");
  }

  let awaitingExpandedSalonSearch = false;

  function isYesAnswer(text) {
      return text === "yes" || text.includes("yes, search") || text === "haan" || text === "ha";
  }

  function isNoAnswer(text) {
      return text === "no" || text === "nahi" || text === "nahin";
  }

  async function findNearbySalons(radiusKm) {
      if (!navigator.geolocation) {
          appendBotMessage("Your browser does not support location access. Please enter a city or salon name manually.");
          return;
      }

      try {
          const position = await new Promise((resolve, reject) => {
              navigator.geolocation.getCurrentPosition(resolve, reject, {
                  enableHighAccuracy: true,
                  timeout: 10000,
                  maximumAge: 0,
              });
          });

          const { latitude, longitude } = position.coords;
          const response = await fetch(`${window.nearbySalonsUrl}?lat=${latitude}&lng=${longitude}&radius=${radiusKm}`);
          const data = await response.json();

          if (!response.ok || data.error) {
              appendBotMessage(data.error || "I could not find nearby salons right now.");
              return;
          }

          const salons = data.salons || [];
          if (!salons.length) {
              if (radiusKm === 5) {
                  awaitingExpandedSalonSearch = true;
                  appendBotMessage(`Aapke 5 km ke andar koi salon registered nahi hai. Kya aap 20 km ke andar salons dekhna chahte hain?<div class="mt-2"><button type="button" class="quick-action" data-message="Yes, search within 20 km">Yes</button><button type="button" class="quick-action ms-2" data-message="No">No</button></div>`);
              } else {
                  appendBotMessage("Sorry, aapke 20 km ke andar bhi koi salon registered nahi hai.");
              }
              return;
          }

          const list = salons.map((salon) => `<div class="mt-2"><strong>${escapeHtml(salon.name)}</strong> • ${salon.distance} km <a href="${salon.url}" target="_blank" rel="noopener">Open</a></div>`).join("");
          const heading = radiusKm === 5
              ? "These salons are near your location:"
              : `${data.total} salon(s) found within 20 km:`;
          appendBotMessage(`${heading}<br>${list}`);
      } catch (error) {
          appendBotMessage("Location access was denied or timed out. Please allow location access to see nearby salons.");
      }
  }

  function appendBotMessage(message) {
      const botResponse = document.createElement("div");
      botResponse.className = "message bot";
      botResponse.innerHTML = message;
      messages.appendChild(botResponse);
      messages.scrollTop = messages.scrollHeight;
  }

  function escapeHtml(value) {
      const element = document.createElement("div");
      element.textContent = value;
      return element.innerHTML;
  }

  function getBotReply(text) {
      const lower = text.toLowerCase();

      if (lower.includes("book") || lower.includes("booking")) {
          return "You can book a service by visiting any salon page and choosing a service. We also support queue booking for quick salon visits.";
      }

      if (lower.includes("service") || lower.includes("services")) {
          return "We offer haircuts, styling, beard grooming, facials, and premium salon packages for men and women.";
      }

      if (lower.includes("time") || lower.includes("timing") || lower.includes("open")) {
          return "Most salons are open from morning to evening. Please check the salon detail page for exact timings.";
      }

      if (lower.includes("salon")) {
          return "You can explore all salons from the home page and open any salon to view services, gallery, and booking details.";
      }

      if (lower.includes("price") || lower.includes("cost")) {
          return "Service prices vary by salon and package. Open a salon page to view the exact price list.";
      }

      return "I can help with salon discovery, booking, service details, and timings. Try asking: book a service, show services, or timings.";
  }
});



let previousCount = 0;
    const salonId = "{{ salon.id }}"; 
    const apiUrl = `/shopkeeper/api/check-queue/${salonId}/`;

    function checkForNewAppointments() {
        fetch(apiUrl)
            .then(response => response.json())
            .then(data => {
                let currentCount = data.pending_count;

                if (currentCount > previousCount) {
                    console.log("🔥 नया कस्टमर आया है! अलार्म बजाओ!");
                    
                   
                    let alarm = document.getElementById("salonAlarm");
                    alarm.play().catch(error => console.log("ब्राउज़र ने आवाज़ रोकी:", error));
                    
                  
                    window.location.reload(); 
                }

                previousCount = currentCount;
            })
            .catch(error => console.error("API Error:", error));
    }

    setInterval(checkForNewAppointments, 5000);
