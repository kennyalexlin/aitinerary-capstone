# Flight Booking Chat App

A conversational AI application for flight booking, featuring a FastAPI backend, Streamlit frontend, LLM-powered extraction and chat, and CSV-based user and chat history persistence.

---

## Features
- **Conversational flight booking assistant** (LLM-powered)
- **User registration and login** (username + email, CSV-based)
- **Automatic extraction of flight details** from user messages
- **Context-aware assistant** that tracks conversation history and only asks for missing info
- **Per-user chat history** saved to CSV files
- **Admin/test endpoint to clear in-memory sessions**
- **Streamlit UI** for chat and user management

---

## Project Structure

```
input_handling_extraction/
│
├── data_persistence/
│   ├── simple_user_system.py   # User registration/authentication (CSV)
│   ├── chat_saver.py          # Save chat messages per user (CSV)
│   ├── users.csv              # Registered users (username, email)
│   └── user_chats/            # Per-user chat history CSVs
│
├── fastapi_app/
│   ├── main.py                # FastAPI app entrypoint
│   ├── extractor.py           # LLM-based flight info extraction
│   ├── routers/
│   │   ├── users.py           # User registration/login endpoints
│   │   └── chat.py            # Chat endpoint, session clearing
│   ├── services/
│   │   ├── chat_service.py    # Chat session logic, LLM, saving
│   │   └── user_service.py    # User management logic
│   └── models/
│       ├── users.py           # Pydantic model for user registration
│       └── chat.py            # Pydantic model for chat requests
│
├── streamlit_app/
│   ├── home.py                # Streamlit frontend (UI for chat and user management)
│   └── logo.png               # App logo
│
├── tests/                     # Backend test scripts
│
├── run_app.sh                 # Script to launch backend and frontend
├── pyproject.toml             # Poetry dependencies
└── README.md                  # This file
```

---

## Setup & Installation

1. **Clone the repo and enter the directory:**
   ```bash
   git clone <repo-url>
   cd input_handling_extraction
   ```
2. **Install dependencies (using Poetry):**
   ```bash
   poetry install
   ```
3. **Run the app:**
   ```bash
   ./run_app.sh
   ```
   This will start both the FastAPI backend (port 8000) and Streamlit frontend (port 8501).

---

## Usage

- **Register/Login:** Use the sidebar in the Streamlit UI to register (username + email) or log in.
- **Chat:** Enter your flight booking queries in the chat tab. The assistant will extract details and ask for missing info.
- **User Management:** View all registered users in the User Management tab.
- **Chat History:** All messages are saved per user in `data_persistence/user_chats/`.
- **Admin:** To clear all in-memory chat sessions (for memory management/testing), send a DELETE request to `/chat/clear_sessions`.

---

## API Endpoints (FastAPI)

- `POST /users/register` — Register a new user (JSON: `{ "username": ..., "email": ... }`)
- `POST /users/login` — Log in (query param: `username`)
- `GET /users` — List all usernames
- `GET /users/table` — List all users with emails
- `POST /chat` — Send a chat message (see models/chat.py for schema)
- `DELETE /chat/clear_sessions` — Clear all in-memory chat sessions

---

## LLM Pipeline

1. **Extraction:**
   - Each user message is sent to an LLM to extract flight info fields (see `extractor.py`).
   - Extracted fields are merged into the session context.
2. **Assistant Response:**
   - The assistant LLM receives the full conversation history and current extracted fields, and generates a context-aware response.

---

## Data Persistence
- **Users:** All registered users are stored in `data_persistence/users.csv`.
- **Chat History:** Each user has a chat history file in `data_persistence/user_chats/`, with all messages (user and assistant) appended as they occur.

---

## Testing
- See the `tests/` folder for backend test scripts.

---

## Dependencies
- Python 3.11+
- FastAPI
- Uvicorn
- Streamlit
- Requests
- Poetry (for dependency management)

---

## Authors
- Michelle Liu <m.liu@berkeley.edu>
