document.addEventListener("DOMContentLoaded", function () {
    document.getElementById("login-submit").addEventListener("click", checkCredentials);
    document.getElementById("password").addEventListener("keyup", function(event){
        event.preventDefault();
        if( event.key === 'Enter'){
            console.log("enter has been clicked")
            document.getElementById("login-submit").click();
        }
    });
    document.getElementById("signup").addEventListener("click", signUpRedir);
});

let logged = false;

let count = 0;

/**
 * Sends an AJAX POST request to the "/processlogin" endpoint to verify user credentials.
 * It retrieves the email and password from the input fields, sends them to the server,
 * and handles the server's response to either redirect to the dashboard on successful login
 * or display an error message on failed login.
 */
function checkCredentials() {
    console.log("credentials is working!")
    var data_d = {
        'email': $('#email').val(),
        'password': $('#password').val()
    };
    console.log('data_d', data_d);

    jQuery.ajax({
        url: "/processlogin",
        data: data_d,
        type: "POST",
        success: function (returned_data) {
            returned_data = JSON.parse(returned_data);

            if (returned_data.success === 1) {
                logged = true;
                window.location.href = "dashboard";
            } else {
                count++;
                $('#failureCount').text(count);
                $('#loginFailure').show();
            }
        },
        error: function () {
            count++;
            $('#failureCount').text(count);
            $('#loginFailure').show();
        }
    });
}

function signUpRedir() {
    console.log("Signing Up...")
    //redirect to either new modem or page to sign up
    window.location.href = "/signup";

}