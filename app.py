# app.py
import nltk
from nltk.stem import PorterStemmer  # ou WordNetLemmatizer
from nltk.corpus import stopwords
import re
from transformers import pipeline
from flask import Flask, request, render_template, jsonify
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
# Onde os arquivos de email serão temporariamente salvos
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['MAX_CONTENT_LENGTH'] = 16 * \
    1024 * 1024  # Limite de 16MB para uploads

# Cria a pasta de uploads se não existir
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# ... (restante do código) ...

if __name__ == '__main__':
    # debug=True para desenvolvimento, mudar para False em produção
    app.run(debug=True)


# app.py (continuação)

# Carregar modelos pré-treinados
# Para classificação: pode usar um modelo BERT para classificação de texto.
# Ex: 'nlptown/bert-base-multilingual-uncased-sentiment' para sentimento,
# ou um modelo treinado especificamente para 'produtivo'/'improdutivo' (o que exige fine-tuning)
# OU usar um modelo de NLI (Natural Language Inference) para verificar se o texto "entaila" as categorias.
# OU usar um LLM (como distilgpt2) para classificar e gerar.

# Para começar, podemos simular a classificação com base em palavras-chave ou usar um modelo de LLM para as duas tarefas.

# Usando um modelo LLM (como distilgpt2 ou gpt2) para classificar e gerar
# (Isso será mais flexível, mas pode exigir um prompt bem elaborado)
# model_name = "distilgpt2" # ou "gpt2"
# generator = pipeline('text-generation', model=model_name)

# --- Opção mais prática e simples para o desafio: Classificador zero-shot e um LLM para gerar respostas ---

# Classificador Zero-Shot (não precisa treinar com seus dados, ele tenta classificar sem exemplos)
classifier = pipeline("zero-shot-classification",
                      model="facebook/bart-large-mnli")

# Gerador de Texto (para respostas)
# gpt2 é um bom ponto de partida
generator = pipeline("text-generation", model="gpt2")


def classify_email(text):
    candidate_labels = ["Produtivo", "Improdutivo"]
    result = classifier(text, candidate_labels, multi_label=False)
    # Exemplo de saída: {'sequence': '...', 'labels': ['Produtivo', 'Improdutivo'], 'scores': [0.98, 0.02]}
    return result['labels'][0]  # Retorna a categoria com maior score


def generate_response(classification, email_text):
    if classification == "Produtivo":
        prompt = f"O email a seguir é produtivo e requer uma resposta. Sugira uma resposta formal e útil:\n'{email_text}'\nResposta:"
        # Para respostas produtivas, o ideal seria ter um modelo que pudesse extrair informações e formatar.
        # Aqui, o LLM vai tentar gerar algo genérico.
    else:  # Improdutivo
        prompt = f"O email a seguir é improdutivo e não requer uma ação imediata. Sugira uma breve mensagem de agradecimento ou confirmação, ou simplesmente ignore. Mensagem sugerida (se necessário):"

    # Gerar a resposta
    response_generation = generator(
        prompt, max_new_tokens=100, num_return_sequences=1, truncation=True)
    # Remove o prompt da resposta gerada
    return response_generation[0]['generated_text'].replace(prompt, '').strip()


# --- Pré-processamento básico ---

try:
    nltk.data.find('corpora/stopwords')
except nltk.downloader.DownloadError:
    nltk.download('stopwords')
try:
    nltk.data.find('corpora/wordnet')
except nltk.downloader.DownloadError:
    nltk.download('wordnet')

# ou 'english' dependendo dos emails
stop_words = set(stopwords.words('portuguese'))
stemmer = PorterStemmer()  # ou WordNetLemmatizer() para lematização


def preprocess_text(text):
    text = text.lower()  # Converter para minúsculas
    text = re.sub(r'\W', ' ', text)  # Remover caracteres não alfanuméricos
    text = re.sub(r'\s+', ' ', text)  # Remover múltiplos espaços em branco
    words = text.split()
    # Remover stop words e aplicar stemming/lematização (opcional, pode ser pesado para zero-shot)
    # words = [stemmer.stem(word) for word in words if word not in stop_words]
    return ' '.join(words)


# app.py (continuação)

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/process_email', methods=['POST'])
def process_email():
    email_content = ""
    # Processar upload de arquivo
    if 'file' in request.files and request.files['file'].filename != '':
        file = request.files['file']
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Ler o conteúdo do arquivo
        try:
            if filename.endswith('.pdf'):
                # Você precisaria de uma biblioteca como 'PyPDF2' ou 'pdfminer.six' para PDFs
                # Ex: from PyPDF2 import PdfReader
                # reader = PdfReader(filepath)
                # for page in reader.pages:
                #    email_content += page.extract_text() or ""
                email_content = "Conteúdo PDF não implementado para leitura automática. Por favor, cole o texto."  # Placeholder
            elif filename.endswith('.txt'):
                with open(filepath, 'r', encoding='utf-8') as f:
                    email_content = f.read()
            else:
                return jsonify({"error": "Formato de arquivo não suportado."}), 400
        finally:
            os.remove(filepath)  # Limpar o arquivo após a leitura

    # Processar texto direto
    elif 'email_text' in request.form and request.form['email_text'] != '':
        email_content = request.form['email_text']
    else:
        return jsonify({"error": "Nenhum arquivo ou texto de email fornecido."}), 400

    if not email_content:
        return jsonify({"error": "O email fornecido está vazio."}), 400

    # Pré-processar o texto
    processed_text = preprocess_text(email_content)

    # Classificar o email
    classification = classify_email(processed_text)

    # Sugerir resposta
    # Use o texto pré-processado ou original, teste qual fica melhor
    suggested_response = generate_response(classification, processed_text)

    return jsonify({
        "category": classification,
        "suggested_response": suggested_response
    })
