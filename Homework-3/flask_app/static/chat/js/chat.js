  var socket;
$(document).ready(function(){

    socket = io.connect('http://' + document.domain + ':' + location.port + '/chat');

    socket.on('connect', function() {
        socket.emit('joined', {});
    });

    socket.on('status', function(data) {
        appendMessage(data.msg, data.style);

    });

     // Handle chat messages from users
    socket.on('message', function(data) {
        console.log("handling chat message");
       appendMessage(data.msg, data.style);
    });

    // Send message when button clicked
    $('#send').click(function() {
        console.log("sending message...")
        sendMessage();
    });

    // Send message when Enter key is pressed
    $('#message').keypress(function(e) {
        if (e.which === 13) { // Enter key
            console.log("sending message...")
            sendMessage();
        }
    });

            // Leave the chat when the leave button is clicked
    $('#leave').click(function() {
        console.log("leaving...")
        socket.emit('left', {});
        window.location.href = "/"; // Redirect to home page
    });


    // Function to send message
    function sendMessage() {
        let message = $('#message').val();
        console.log(message);
        if (message.trim() !== '') {
            socket.emit('text', {
                msg: message,
                user: "{{ user|safe }}"

            });
            $('#message').val('').focus();
        }
    }

    function appendMessage(message, style) {
         console.log("appending");
        let tag  = document.createElement("p");
        let text = document.createTextNode(message);
        let chatBox = document.getElementById("chat");
        tag.appendChild(text);
        tag.style.cssText = style;
        chatBox.appendChild(tag);
        $('#chat').scrollTop(chatBox.scrollHeight);
    }

});