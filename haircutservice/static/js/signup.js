const signupForm = document.getElementById("signupForm");

if (signupForm) {
    signupForm.addEventListener('submit', function (event) {
        const password = document.getElementById('password').value.trim();
        const confirmPassword = document.getElementById('confirm_password').value.trim();
        const phone = document.getElementById("phonenumber").value.trim();
        const errorBox = document.getElementById('jsPasswordError');

        // Validate password confirmation
        if (password.length < 10) {
            event.preventDefault();
            errorBox.textContent = "Password must be at least 10 characters long.";
            errorBox.classList.remove('d-none');
            return;
        }
        if (password !== confirmPassword) {
            event.preventDefault();
            errorBox.textContent = "Password and confirm password must be the same!";
            errorBox.classList.remove('d-none');
            return;
        }

        // Validate phone number
        if (!/^\d{10}$/.test(phone)) {
            event.preventDefault();
            errorBox.textContent = "Mobile number must be exactly 10 digits.";
            errorBox.classList.remove("d-none");
            return;
        }

        errorBox.classList.add('d-none');
    });
}