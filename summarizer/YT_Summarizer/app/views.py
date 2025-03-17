from django.shortcuts import render
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from transformers import pipeline
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

nltk.download('punkt')
nltk.download('stopwords')

# Initialize the summarization pipeline once
summarizer = pipeline('summarization', model='facebook/bart-large-cnn', min_length=30, max_length=100)

def index(request):
    return render(request, 'index.html')

def split_text_into_chunks(text, max_length):
    words = word_tokenize(text)
    chunks = []
    current_chunk = []
    current_length = 0

    for word in words:
        current_chunk.append(word)
        current_length += len(word) + 1

        if current_length >= max_length:
            chunks.append(' '.join(current_chunk))
            current_chunk = []
            current_length = 0

    if current_chunk:
        chunks.append(' '.join(current_chunk))

    return chunks

def calculate_similarity(text1, text2):
    stop_words = set(stopwords.words('english'))
    tokens1 = [word for word in word_tokenize(text1.lower()) if word.isalnum() and word not in stop_words]
    tokens2 = [word for word in word_tokenize(text2.lower()) if word.isalnum() and word not in stop_words]

    vectorizer = CountVectorizer().fit_transform([text1, text2])
    vectors = vectorizer.toarray()

    cosine_sim = cosine_similarity(vectors)
    return cosine_sim[0, 1]

def get_transcript_and_subtitles(video_id):
    transcript = YouTubeTranscriptApi.get_transcript(video_id)
    transcript_text = " ".join([entry['text'] for entry in transcript])
    
    formatter = TextFormatter()
    subtitle_text = formatter.format_transcript(transcript)
    
    return transcript_text, subtitle_text

def get_transcript_long(request):
    if request.method == 'POST':
        video_id = request.POST.get('video_id')

        try:
            transcript_text, subtitle_text = get_transcript_and_subtitles(video_id)
            long_text = transcript_text

            chunks = split_text_into_chunks(long_text, 2300)
            summaries = []
            for chunk in chunks:
                summary = summarizer(chunk, max_length=100, do_sample=False)
                summaries.append(summary[0]['summary_text'])

            final_summary = '. '.join(summaries)
            similarity_score = calculate_similarity(transcript_text, subtitle_text)
            
            return render(request, 'transcript.html', {'transcript':transcript_text,'len_transcript':len(transcript_text),'summary': final_summary, 'len_summary':len(final_summary),'similarity_score': similarity_score})
        except Exception as e:
            return render(request, 'transcript.html', {'error': str(e)})
    return render(request, 'index.html')
