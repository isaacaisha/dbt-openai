$(document).ready(function () {
    function loadMessages() {
        $.ajax({
            type: 'GET',
            url: window.loadMessagesUrl,
            success: function (response) {
                $("#display").empty();
                response.messages.forEach(function (message) {
                    var temp = `
                        <div class="message-container">
                            <div class="message-header">
                                <b>${message.user}</b>
                                <span class="time-left">${message.date}</span>
                            </div>
                            <div class="message-body" style="color: #faf;">
                                ${message.value}
                            </div>
                        </div>
                        <hr class='gold mb-3'>
                    `;
                    $("#display").append(temp);
                });
            },
            error: function (response) {
                alert('An error occurred while loading messages.');
            }
        });
    }

    setInterval(loadMessages, 1000); // Refresh messages every second

    $('#chat-form').on('submit', function (e) {
        e.preventDefault();

        $.ajax({
            type: 'POST',
            url: window.chatFormUrl,
            data: {
                username: $('input[name="username"]').val(),
                theme_id: $('input[name="theme_id"]').val(),
                message: $('textarea[name="message"]').val(),
                csrf_token: $('input[name="csrf_token"]').val(),
            },
            success: function (data) {
                $('textarea[name="message"]').val(''); // Clear the message input
                loadMessages(); // Refresh messages
            },
            error: function (response) {
                alert('An error occurred while sending your message.');
            }
        });
    });
});
