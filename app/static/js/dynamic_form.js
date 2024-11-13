document.addEventListener('DOMContentLoaded', function() {
    const updateForm = () => {
        const contentType = document.getElementById('id_contentType');
        if (contentType && contentType.value.includes('image')) {
            const textInput = document.getElementById('id_content');
            if (textInput) {
                textInput.parentElement.style.display = 'none';
            }

            const imageInput = document.getElementById('id_image');
            if (imageInput) {
                imageInput.parentElement.style.display = 'flex';
            }
        } else {
            const imageInput = document.getElementById('id_image');
            if (imageInput) {
                imageInput.parentElement.style.display = 'none';
            }

            const textInput = document.getElementById('id_content');
            if (textInput) {
                textInput.parentElement.style.display = 'flex';
            }
        }
    };

    const contentType = document.getElementById('id_contentType');
    if (contentType) {
        updateForm();
        contentType.addEventListener('change', updateForm);
    }
});
