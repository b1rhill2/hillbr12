document.addEventListener("DOMContentLoaded", function () {
    document.getElementById("signup-submit").addEventListener("click", signUp);
    document.getElementById("password").addEventListener("keyup", function (event) {
        event.preventDefault();
        if (event.key === 'Enter') {
            console.log("enter has been clicked")
            document.getElementById("signup-submit").click();
        }
    });
});

const validateEmail = (email) => {
    if(email === undefined){
        return false;
    }else {
        return email.match(
            /^(([^<>()[\]\\.,;:\s@\"]+(\.[^<>()[\]\\.,;:\s@\"]+)*)|(\".+\"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/
        );
    }
};

function validate() {
    console.log("validating...");
    const email = $('#email').val();
    const password = $('#password').val();
    const confirmPassword = $('#conf-password').val();

    if(!email || null){
        return{ valid: false, code: 6}
    }
    if(email){
        if(validateEmail(email)){
             if (!password) {
                return { valid: false, code: 3 };
            }
             if(password.length < 8){
                return{ valid: false, code: 5}
            }
            if (!confirmPassword) {
                return { valid: false, code: 2 };
            }
            if (password !== confirmPassword) {
                return { valid: false, code: 4 };
            }

            return { valid: true, code: 1 };
        }else{
           return { valid: false, code: 6};

        }
    }
}

function signUp(){
    //check if passwords match
    // Hide all possible alerts first
    $('#loginFailure, #loginFailure2, #loginFailure3, #loginFailure4, #loginFailure5, #loginFailure6, #loginFailure7').hide();

    const validation = validate();
    if(validation.valid) {

        //gets users information
        //save email
        //save password
        //set role to user
        var data_d = {
            'email': $('#email').val(),
            'password': $('#password').val(),
            'role': "user"
        };

        console.log('data_d', data_d);
        //store new users data
        jQuery.ajax({
            url: "/processSignup",
            data: data_d,
            type: "PUT",

            success: function (returned_data) {
                returned_data = JSON.parse(returned_data);
                //redirect back to login
                if (returned_data.success === 1) {
                    logged = true;
                    window.location.href = "/login";
                } else {
                    console.log("Data Incomplete")
                    $('#loginFailure7').show();
                }
            },
            error: function () {
                console.log("Data Incomplete")
                $('#loginFailure7').show();
            }
        });
     } else {
        //hide all first
        $('#loginFailure, #loginFailure2, #loginFailure3, #loginFailure4, #loginFailure5, #loginFailure6, #loginFailure7').hide();

        //show specific error
        $(`#loginFailure${validation.code}`).text(validation.message).show();
    }
}
