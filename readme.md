# AI Bookstore with Ollama Llama

A modern web-based bookstore application with an integrated AI chatbot powered by Ollama's Llama models for personalized book recommendations.

## Features

- **Book Search**: Search millions of books using the OpenLibrary database
- **Ollama Llama AI Chatbot**: Get personalized book recommendations through natural language conversation with local Llama models
- **Shopping Cart**: Add books to cart and manage your selections
- **Beautiful UI**: Clean, responsive interface built with Streamlit

## Prerequisites

- **Ollama**: Install Ollama from [ollama.ai](https://ollama.ai) and have it running
- **Llama Model**: Pull a Llama model (e.g., `ollama pull llama3.2`)

## Installation

1. Clone this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Start Ollama (if not already running):
   ```bash
   ollama serve
   ```

2. Run the application:
   ```bash
   streamlit run app.py
   ```

3. Open your browser to `http://localhost:8501` to start using the bookstore.

## Features Overview

### 🔍 Search Books
- Search by title, author, genre, or any keyword
- View book covers, details, and genres
- Add books directly to your cart

### 🤖 Ollama Llama AI Assistant
- Chat with your local Llama model for recommendations
- The AI understands natural language and can perform actions like searching and managing cart
- Ask for books by genre, theme, author, or mood
- AI can automatically search for books and add them to cart based on conversation

### 🛒 Shopping Cart
- View all books in your cart
- Remove individual items or clear the entire cart
- See total number of items

## Technology Stack

- **Frontend**: Streamlit
- **Backend API**: OpenLibrary API
- **AI Model**: Ollama Llama models (local inference)
- **Language**: Python
- **Libraries**: ollama, requests, streamlit

## AI Capabilities

The Ollama Llama AI assistant can:
- Understand book recommendation requests
- Automatically search the OpenLibrary database
- Add books to cart by number
- View and manage shopping cart
- Provide natural language responses
- Remember conversation context

## Configuration

The app uses the `llama3.2` model by default. To use a different model:
- Pull the model: `ollama pull <model_name>`
- Update the model name in `app.py` in the `ollama.chat()` call

## Contributing

Feel free to submit issues and enhancement requests!