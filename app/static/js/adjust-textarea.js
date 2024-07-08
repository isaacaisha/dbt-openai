function adjustTextareaHeight(textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = (textarea.scrollHeight) + 'px';
}

document.addEventListener("DOMContentLoaded", function () {
    var textareas = document.querySelectorAll('.textarea_details');
    textareas.forEach(function (textarea) {
        adjustTextareaHeight(textarea);
        textarea.addEventListener('input', function () {
            adjustTextareaHeight(textarea);
        });
    });
});
