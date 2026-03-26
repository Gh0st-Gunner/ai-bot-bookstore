import streamlit as st
import requests
import ollama
import re

# Session state initialization
if 'cart' not in st.session_state:
    st.session_state.cart = []
if 'last_books' not in st.session_state:
    st.session_state.last_books = []
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'bought' not in st.session_state:
    st.session_state.bought = []
if 'ai_available' not in st.session_state:
    st.session_state.ai_available = False

def search_books(query):
    """Search books using OpenLibrary API"""
    url = f"https://openlibrary.org/search.json?q={query}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        books = []
        for doc in data.get('docs', [])[:10]:  # Limit to 10 results
            book = {
                'title': doc.get('title', 'Unknown'),
                'author': doc.get('author_name', ['Unknown'])[0] if doc.get('author_name') else 'Unknown',
                'year': doc.get('first_publish_year', 'Unknown'),
                'subjects': doc.get('subject', []),
                'cover_id': doc.get('cover_i')
            }
            books.append(book)
        return books
    except Exception as e:
        st.error(f"Error searching books: {e}")
        return []

def add_to_cart(book):
    """Add a book to the cart"""
    st.session_state.cart.append(book)

def remove_from_cart(title):
    """Remove a book from the cart by title"""
    st.session_state.cart = [b for b in st.session_state.cart if b['title'].lower() != title.lower()]

def clear_cart():
    """Clear the cart"""
    st.session_state.cart = []

def process_input_fallback(user_input):
    """Handle basic search/cart operations when AI is unavailable."""
    text = user_input.strip()
    lower_text = text.lower()
    executed_actions = []

    if any(k in lower_text for k in ["view cart", "show cart", "cart"]):
        if not st.session_state.cart:
            executed_actions.append("🛒 Your cart is empty.")
        else:
            cart_info = "🛒 Your Cart:\n"
            for i, book in enumerate(st.session_state.cart, 1):
                cart_info += f"{i}. {book['title']} — {book['author']}\n"
            cart_info += f"\nTotal: {len(st.session_state.cart)} items"
            executed_actions.append(cart_info)

    if "clear cart" in lower_text:
        clear_cart()
        executed_actions.append("Cart cleared")

    if "remove " in lower_text:
        remove_title = text[lower_text.find("remove ") + len("remove "):].strip()
        if remove_title:
            remove_from_cart(remove_title)
            executed_actions.append(f"Removed '{remove_title}' from cart")

    add_match = re.search(r"\badd\s+(\d+)\b", lower_text)
    if add_match:
        idx = int(add_match.group(1)) - 1
        if st.session_state.last_books and 0 <= idx < len(st.session_state.last_books):
            book = st.session_state.last_books[idx]
            add_to_cart(book)
            executed_actions.append(f"Added '{book['title']}' to cart")
        else:
            executed_actions.append("Couldn't add that book. Search first and use 'add <number>'.")

    should_search = any(k in lower_text for k in ["search", "find", "books about", "recommend"])
    if should_search:
        query = text
        for prefix in ["search", "find", "books about", "recommend", "recommend books"]:
            query = re.sub(rf"^\s*{re.escape(prefix)}\s*", "", query, flags=re.IGNORECASE)
        query = query.strip() or "books"
        books = search_books(query)
        st.session_state.last_books = books
        executed_actions.append(f"Searched for '{query}' and found {len(books)} books")

    if not executed_actions:
        return (
            "I'm currently running in offline assistant mode because Ollama is not connected. "
            "You can still use chat commands like:\n"
            "- search <query>\n"
            "- add <number>\n"
            "- view cart\n"
            "- remove <title>\n"
            "- clear cart"
        )

    return "Offline assistant mode (Ollama unavailable):\n\n" + "\n".join(executed_actions)

def process_input(user_input):
    """Process user input using Ollama Llama model"""
    if not st.session_state.ai_available:
        return process_input_fallback(user_input)

    system_prompt = """You are an AI bookstore assistant. Help users discover books using the OpenLibrary API.

Available actions (include these commands in your response when appropriate):

- To search for books, include: SEARCH: [query]
- To add a book to cart, include: ADD: [number] (1-based index from last search results)
- To view cart, include: VIEW_CART
- To remove from cart, include: REMOVE: [title]
- To clear cart, include: CLEAR_CART

Always respond helpfully. For recommendations, suggest searching first. Keep responses concise."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input}
    ]
    
    try:
        response = ollama.chat(model='llama3.2', messages=messages)
        response_text = response['message']['content']
    except Exception as e:
        return f"Error communicating with AI model: {e}"
    
    # Parse for commands
    executed_actions = []
    
    if "SEARCH:" in response_text:
        # Extract query
        search_part = response_text.split("SEARCH:")[1].split("\n")[0].strip()
        query = search_part if search_part else user_input.replace("recommend", "").replace("books about", "").strip()
        books = search_books(query)
        st.session_state.last_books = books
        executed_actions.append(f"Searched for '{query}' and found {len(books)} books")
    
    if "ADD:" in response_text:
        add_part = response_text.split("ADD:")[1].split()[0].strip()
        try:
            idx = int(add_part) - 1
            if st.session_state.last_books and 0 <= idx < len(st.session_state.last_books):
                book = st.session_state.last_books[idx]
                add_to_cart(book)
                executed_actions.append(f"Added '{book['title']}' to cart")
        except:
            pass
    
    if "VIEW_CART" in response_text:
        if not st.session_state.cart:
            cart_info = "🛒 Your cart is empty."
        else:
            cart_info = "🛒 Your Cart:\n"
            for i, book in enumerate(st.session_state.cart, 1):
                cart_info += f"{i}. {book['title']} — {book['author']}\n"
            cart_info += f"\nTotal: {len(st.session_state.cart)} items"
        executed_actions.append(cart_info)
    
    if "REMOVE:" in response_text:
        remove_part = response_text.split("REMOVE:")[1].split("\n")[0].strip()
        remove_from_cart(remove_part)
        executed_actions.append(f"Removed '{remove_part}' from cart")
    
    if "CLEAR_CART" in response_text:
        clear_cart()
        executed_actions.append("Cart cleared")
    
    # Return the AI response with executed actions
    final_response = response_text
    if executed_actions:
        final_response += "\n\n" + "\n".join(executed_actions)
    
    return final_response

def main():
    st.set_page_config(
        page_title="AI Bookstore",
        page_icon="📚",
        layout="wide"
    )
    
    st.title("📚 AI Bookstore with Ollama Llama")
    st.markdown("Discover your next favorite book with our AI-powered Ollama Llama assistant!")
    
    # Check if Ollama is running
    try:
        ollama.list()
        st.session_state.ai_available = True
        st.success("✅ Connected to Ollama")
    except:
        st.session_state.ai_available = False
        st.warning("⚠️ Ollama is not connected. Search, browse, and cart still work, and chat runs in basic offline mode.")
    
    # Sidebar AI Chat
    with st.sidebar:
        st.header("🤖 Ollama Llama AI Assistant")
        if st.session_state.ai_available:
            st.markdown("Chat with our Ollama-powered Llama AI for personalized book recommendations!")
        else:
            st.markdown("Ollama is offline. Use basic commands: `search <query>`, `add <number>`, `view cart`, `remove <title>`, `clear cart`.")
        
        # Chat container
        chat_container = st.container(height=400)
        with chat_container:
            for message in st.session_state.messages:
                with st.chat_message(message['role']):
                    st.markdown(message['content'])
        
        # Chat input
        if prompt := st.chat_input("Ask me about books..."):
            st.session_state.messages.append({'role': 'user', 'content': prompt})
            response = process_input(prompt)
            st.session_state.messages.append({'role': 'assistant', 'content': response})
            st.rerun()
    
    # Main content tabs
    tab1, tab2, tab3, tab4 = st.tabs(["🔍 Search Books", "📖 Browse & Recommend", "🛒 Shopping Cart", "📦 Bought"])
    
    with tab1:
        st.header("Search Books")
        st.markdown("Find books by title, author, genre, or any keyword.")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            query = st.text_input("Enter your search query", placeholder="e.g., 'Harry Potter', 'science fiction', 'J.K. Rowling'")
        with col2:
            search_button = st.button("🔍 Search", use_container_width=True)
        
        if search_button and query:
            with st.spinner("Searching for books..."):
                books = search_books(query)
            st.session_state.last_books = books
            if not books:
                st.error("No books found. Try different keywords or check your spelling.")

        if st.session_state.last_books:
            st.success(f"Found {len(st.session_state.last_books)} books")

            for i, book in enumerate(st.session_state.last_books):
                with st.container():
                    col1, col2, col3 = st.columns([1, 2, 1])

                    with col1:
                        if book['cover_id']:
                            st.image(
                                f"https://covers.openlibrary.org/b/id/{book['cover_id']}-M.jpg",
                                width=80,
                                caption="Cover"
                            )
                        else:
                            st.markdown("📖\n*No cover*")

                    with col2:
                        st.subheader(book['title'])
                        st.write(f"**Author:** {book['author']}")
                        st.write(f"**Published:** {book['year']}")
                        genres = ', '.join(book['subjects'][:3]) if book['subjects'] else 'Not specified'
                        st.write(f"**Genres:** {genres}")

                    with col3:
                        st.write("")  # Spacer
                        if st.button(f"➕ Add to Cart", key=f"add_{i}", use_container_width=True):
                            add_to_cart(book)
                            st.success(f"Added '{book['title']}' to cart!")
                            st.rerun()

                    st.divider()
    
    with tab2:
        st.header("AI-Powered Recommendations")
        if st.session_state.ai_available:
            st.markdown("""
        Use the Llama AI assistant in the sidebar to get personalized recommendations!
        
        The AI can understand natural language and help you discover books based on:
        - Genres and themes
        - Authors and series
        - Mood and preferences
        - Similar books to ones you like
        """)
        else:
            st.markdown("""
        Ollama is currently offline.

        You can still:
        - Search books in the Search tab
        - Add/remove books from your cart
        - Use basic sidebar chat commands (`search`, `add`, `view cart`, `remove`, `clear cart`)
        """)
        
        if st.session_state.last_books:
            st.subheader("Recent Search Results")
            st.markdown("Books from your last search:")
            for book in st.session_state.last_books[:5]:  # Show first 5
                st.write(f"• **{book['title']}** by {book['author']} ({book['year']})")
    
    with tab3:
        st.header("Your Shopping Cart")
        
        if st.session_state.cart:
            st.markdown(f"**Total items:** {len(st.session_state.cart)}")
            
            for i, book in enumerate(st.session_state.cart):
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    st.write(f"**{book['title']}**")
                    st.write(f"*by {book['author']}*")
                with col2:
                    st.write(f"{book['year']}")
                with col3:
                    if st.button("❌ Remove", key=f"remove_{i}"):
                        remove_from_cart(book['title'])
                        st.success(f"Removed '{book['title']}' from cart")
                        st.rerun()
                st.divider()
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🗑️ Clear Cart", use_container_width=True):
                    clear_cart()
                    st.success("Cart cleared!")
                    st.rerun()
            with col2:
                if st.button("💳 Checkout", use_container_width=True, type="primary"):
                    st.session_state.bought.extend(st.session_state.cart)
                    clear_cart()
                    st.success("✅ Thank you for shopping!")
                    st.rerun()
        else:
            st.info("Your cart is empty. Start by searching for books or asking the AI assistant for recommendations!")

    with tab4:
        st.header("📦 Bought Books")

        if st.session_state.bought:
            st.markdown(f"**Total purchased:** {len(st.session_state.bought)} book(s)")
            st.divider()

            for i, book in enumerate(st.session_state.bought):
                col1, col2 = st.columns([1, 3])
                with col1:
                    if book.get('cover_id'):
                        st.image(
                            f"https://covers.openlibrary.org/b/id/{book['cover_id']}-M.jpg",
                            width=70,
                        )
                    else:
                        st.markdown("📖\n*No cover*")
                with col2:
                    st.subheader(book['title'])
                    st.write(f"**Author:** {book['author']}")
                    st.write(f"**Published:** {book['year']}")
                st.divider()

            if st.button("🗑️ Clear History", use_container_width=True):
                st.session_state.bought = []
                st.rerun()
        else:
            st.info("No purchased books yet. Add books to your cart and checkout!")

if __name__ == "__main__":
    main()