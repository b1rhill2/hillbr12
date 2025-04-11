document.addEventListener("DOMContentLoaded", function () {
    document.getElementById("login-submit").addEventListener("click", checkCredentials);
    document.getElementById("password").addEventListener("keyup", function(event){
        event.preventDefault();
        if( event.key === 'Enter'){
            console.log("enter has been clicked")
            document.getElementById("login-submit").click();
        }
    });
});

let logged = false;

let count = 0;


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
                window.location.href = "/home";
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