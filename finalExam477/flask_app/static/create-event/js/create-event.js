document.addEventListener("DOMContentLoaded", function () {
    // Prevent the default form submission behavior
    document.getElementById("create-event-form").addEventListener("submit", function(event) {
        event.preventDefault();
        createEvent();
    });

    document.getElementById("submit").addEventListener("click", function(event) {
        event.preventDefault();
        createEvent();
    });

    document.getElementById("submit").addEventListener("keyup", function (event) {
        if (event.key === 'Enter') {
            console.log("enter has been clicked")
            event.preventDefault();
            createEvent();
        }
    });
});

/**
 * Sends an AJAX POST request to the "/processCreateEvent" endpoint to create a new event.
 * It gathers event details (name, dates, times, invitees) from the form inputs,
 * logs the data to the console, and handles the server's response.
 * On success, it redirects the user to the newly created event's page.
 * On failure, it displays an error message.
 */
function createEvent(){
    var data_d = {
       'eventName': $("#eventName").val(),
        'startDate': $("#startDate").val(),
        'endDate': $("#endDate").val(),
        'startTime': $("#startTime").val(),
        'endTime': $("#endTime").val(),
        'invitees': $("#invitees").val(),
    };

    console.log('data_d', data_d);

    jQuery.ajax({
        url: "/processCreateEvent",
        data: data_d,
        type: "POST",
        contentType: "application/x-www-form-urlencoded",
        success: function (returned_data) {
            returned_data = JSON.parse(returned_data);
            if (returned_data.success === 1) {
                console.log("Success!");
                //window.location.href = "/dashboard";
                //bring to scheduled event
                 window.location.href = "/event/" + returned_data.event_id;
            } else {
                console.log("Data Incomplete");
                $('#forumFailure').show();
            }
        },
        error: function () {
            console.log("Data Incomplete");
            $('#forumFailure').show();
        }
    });
}
