//JavaScript code to handle like / unlike
$(document).ready(function () {
    // Handle click event on like button
    $('.like-button').click(function () {
        var conversationId = $(this).data('conversation-id');
        var button = $(this); // Store reference to the button

        // Toggle liked status
        var liked = button.hasClass('liked') ? 0 : 1;

        // Send AJAX request to update liked status
        $.ajax({
            url: '/update-like/' + conversationId,
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ liked: liked }),
            success: function (response) {
                // Toggle the 'liked' class on the button
                button.toggleClass('liked');

                // Update button background color based on liked status
                if (liked) {
                    button.css('color', 'pink');
                } else {
                    button.css('color', 'lightcyan');
                }
            },
            error: function (xhr, status, error) {
                console.error('Error:', error);
            }
        });
    });
});
