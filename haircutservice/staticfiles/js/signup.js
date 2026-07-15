const signupForm = document.getElementById("signupForm")

if(signupForm){
    signupForm.addEventListener('submit', function(event){
        const password = document.getElementById('password').value.trim();
        const confirmpassword = document.getElementById('confirm_password').value.trim();
        const errorBox = document.getElementById('jsPasswordError');

        if (password !== confirmpassword ){
            console.log("Pehla Password hai: ->" + password + "<-");
            console.log("Dusra Password hai: ->" + confirmpassword + "<-");
            event.preventDefault();
            errorBox.textContent = "Password and confirm password must be same!";
            errorBox.classList.remove('d-none');
        }
        else{
            errorBox.classList.add('d-none');
        }
    });
}