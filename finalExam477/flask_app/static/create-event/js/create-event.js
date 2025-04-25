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
