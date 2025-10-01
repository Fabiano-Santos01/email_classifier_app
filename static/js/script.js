document.getElementById('emailForm').addEventListener('submit', async function(event) {
    event.preventDefault(); // Impede o envio padrão do formulário

    const fileInput = document.getElementById('fileUpload');
    const emailTextInput = document.getElementById('emailTextInput');
    const loadingDiv = document.getElementById('loading');
    const resultsDiv = document.getElementById('results');
    const errorDiv = document.getElementById('error');

    resultsDiv.style.display = 'none';
    errorDiv.style.display = 'none';
    loadingDiv.style.display = 'block';

    const formData = new FormData();
    if (fileInput.files.length > 0) {
        formData.append('file', fileInput.files[0]);
    } else if (emailTextInput.value.trim() !== '') {
        formData.append('email_text', emailTextInput.value.trim());
    } else {
        loadingDiv.style.display = 'none';
        errorDiv.style.display = 'block';
        document.getElementById('errorMessage').innerText = 'Por favor, carregue um arquivo ou cole o texto do e-mail.';
        return;
    }

    try {
        const response = await fetch('/process_email', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (response.ok) {
            document.getElementById('categoryResult').innerText = data.category;
            document.getElementById('responseResult').innerText = data.suggested_response;
            resultsDiv.style.display = 'block';
        } else {
            errorDiv.style.display = 'block';
            document.getElementById('errorMessage').innerText = data.error || 'Erro desconhecido ao processar o e-mail.';
        }
    } catch (e) {
        errorDiv.style.display = 'block';
        document.getElementById('errorMessage').innerText = 'Falha na comunicação com o servidor: ' + e.message;
    } finally {
        loadingDiv.style.display = 'none';
    }
});