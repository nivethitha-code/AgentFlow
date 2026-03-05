# 🤖 AgentFlow — Agentic Workflow Builder

> An AI-powered platform to design, execute, and monitor multi-step agentic workflows — all in one intelligent automation studio.

---

## 🔗 Live Demo & Screenshots

🌐 **Deployed App:** [agent-flow.vercel.app](https://agent-flow-blush.vercel.app)

| Home | Workflow Builder | Execution View | History |
|-----------------|-----------------|----------------|----------------|
| <img width="1297" height="610" alt="image" src="https://github.com/user-attachments/assets/9e1e38e6-18ac-4ae9-8fc5-6d7e5b7379d5" /> | <img width="1297" height="610" alt="image" src="https://github.com/user-attachments/assets/02c763e6-c0fc-43fa-89bc-e177330ee82d" />   <img width="1297" height="610" alt="image" src="https://github.com/user-attachments/assets/878e0be4-06a1-4a07-91ef-71823c3d183a" />    | <img width="1297" height="610" alt="image" src="https://github.com/user-attachments/assets/3c440596-4ec5-4692-869d-62d742b1002f" /> | <img width="1297" height="610" alt="image" src="https://github.com/user-attachments/assets/cd53671e-49fb-42c6-8a16-9c5b8597a0e5" /> |

---

## 🧱 Tech Stack

![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)
![Vite](https://img.shields.io/badge/Vite-646CFF?style=for-the-badge&logo=vite&logoColor=white)
![Framer Motion](https://img.shields.io/badge/Framer_Motion-0055FF?style=for-the-badge&logo=framer&logoColor=white)
![TailwindCSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![Supabase](https://img.shields.io/badge/Supabase-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white)
![Groq](https://img.shields.io/badge/Groq_API-F55036?style=for-the-badge&logo=groq&logoColor=white)
![Render](https://img.shields.io/badge/Render-46E3B7?style=for-the-badge&logo=render&logoColor=white)
![Vercel](https://img.shields.io/badge/Vercel-000000?style=for-the-badge&logo=vercel&logoColor=white)

---

## 🚀 Installation & Setup

**Backend**
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Frontend**
```bash
cd frontend
npm install
npm run dev
```

**Environment Variables**

`backend/.env`
```
API_KEY=your_groq_api_key
API_URL=https://api.groq.com/openai/v1/chat/completions
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
FRONTEND_URL=http://localhost:5173
```

`frontend/.env`
```
VITE_API_URL=http://localhost:8000
VITE_SUPABASE_URL=your_supabase_project_url
VITE_SUPABASE_KEY=your_supabase_anon_key
```

**Database Setup (Supabase)**

Run the following SQL in your Supabase SQL Editor:
```sql
-- Run the schema.sql file provided in /backend/schema.sql
```

---

## 💡 Usage

- Click **"Create a New Workflow"** on the Home page and give it a name
- Add steps in the **Workflow Builder** — choose a step type, model, and write a prompt
- Select **Completion Criteria** for each step to ensure quality output
- Click **Save & Run** to execute the workflow and watch it run in real-time
- View all past runs in **Execution History**, re-run or delete them as needed

---

## ✨ Features

**🏠 Home & Navigation**
- Landing page with a hero section and a prominent "Create a New Workflow" button
- Clean naming modal that prompts for a workflow name before entering the builder
- Navigation tabs for Home and Execution History
- Light/Dark mode toggle powered by `next-themes`

**🛠️ Workflow Builder**
- Add multiple steps to a workflow, each fully configurable independently
- **Step Types:**
  - `Normal Task (Sequential)` — executes one after another, passing output as context
  - `Router / Manager (Condition-based)` — inspects LLM output and routes to a specific branch using label matching
  - `Parallel Spawner` — spawns multiple steps to execute simultaneously using `asyncio.gather()`
- **Model Selection per Step:** Choose from Llama 3.3 70B, Llama 3.1 8B, or Mixtral 8x7B (via Groq API)
- **Prompt Templates** with `{{context}}` placeholder to inject previous step's output
- **Branch Management** for Router and Parallel steps — add/remove branches with label and step linking
- Animated step cards with connector lines built using Framer Motion

**✅ Completion Criteria & Smart Retry**
- **Contains Text** — validates that the LLM output includes all specified comma-separated keywords
- **Valid JSON** — strictly parses the response and ensures it is a valid JSON object or array
- **LLM Judge (AI Check)** — uses Llama 3.1 8B as an impartial judge to evaluate if the output meets a custom instruction
- If validation fails, the system automatically refines the prompt and retries up to **3 times**
- On retry after `json_valid` failure, the system explicitly reminds the model to return raw JSON only

**⚡ Real-time Execution View**
- Live step-by-step execution status displayed as a vertical timeline
- Per-step status icons: ✅ Completed, 🔄 Running, ❌ Failed, ⏳ Pending
- Shows retry count badge on steps that needed retries
- Input context and full LLM output displayed per step in a monospace panel
- **Supabase Realtime** push subscription on `workflow_runs` table for instant UI updates without polling
- 🎉 Confetti celebration animation fires on successful workflow completion
- **Re-run** button triggers a fresh execution of the entire workflow
- **Individual step re-run** button on each step card for targeted debugging
- **Delete Workflow** button permanently removes the workflow and all its runs

**📋 Execution History**
- Lists all past runs with workflow name, timestamp, and status (color-coded)
- Click any run card to navigate to its Execution View
- Delete individual runs directly from the history list (hover to reveal button)

**⚙️ Backend API**
- Built with **FastAPI** — async-first, auto-documented via `/docs`
- **Graph-based workflow execution engine** — resolves step order dynamically using `order` field and `next_steps` links
- Parallel steps executed concurrently using `asyncio.gather()`
- Router step output matched against branch labels with a `DEFAULT` fallback
- Automatic context merging when a step follows multiple parallel branches
- Custom lightweight **Supabase client** built with `httpx` — no SDK dependency
- **Pydantic v2 models** for strict request/response validation
- CORS configured for cross-origin requests between Vercel frontend and Render backend
- Background tasks via FastAPI `BackgroundTasks` so workflow execution is non-blocking

**🗄️ Database**
- 2 Supabase PostgreSQL tables: `workflows` (stores step definitions as JSONB) and `workflow_runs` (stores execution state and step results as JSONB)
- UUID primary keys auto-generated with `uuid-ossp` extension
- Cascade delete: removing a workflow automatically removes all its runs
- Supabase Realtime enabled on `workflow_runs` for live frontend subscriptions

---

## 📚 Key Learnings & Challenges

- **Graph-based execution engine**: Designing the backend to support non-linear step graphs (sequential, parallel, and router) required dynamic traversal of the step graph rather than a simple ordered loop — this was the core algorithmic challenge of the project
- **Parallel context merging**: When a step follows two parallel branches, automatically merging their outputs into a single labeled context string required careful tracking of `last_batch_outputs` across execution batches
- **Router condition matching**: Matching LLM output against user-defined branch labels (e.g., "TECHNICAL") required case-insensitive substring matching with a `DEFAULT` fallback to avoid dead ends in routing
- **Smart retry prompt engineering**: Simply retrying with the original prompt after failure did not improve results — prepending an explicit failure notice and reminder dramatically improved LLM compliance, especially for `json_valid` criteria
- **Realtime without polling**: Using Supabase Realtime subscriptions on the `workflow_runs` table eliminated the need for periodic polling in the frontend, giving genuinely live execution updates with zero extra API calls
- **Custom Supabase client**: The official Supabase Python SDK had compatibility issues, so a lightweight custom HTTP client was built using `httpx` that directly calls the PostgREST API with the same interface pattern

---

## 🗂️ Project Structure

```
AgentFlow/
├── backend/
│   ├── app/
│   │   ├── main.py        # FastAPI app + all API endpoints + execution engine
│   │   ├── models.py      # Pydantic models (Step, Workflow, RunResult, etc.)
│   │   ├── service.py     # LLMService — Groq API calls + output validation
│   │   └── database.py    # Custom Supabase HTTP client (httpx-based)
│   ├── schema.sql         # Supabase table setup SQL
│   ├── requirements.txt   # Python dependencies
│   └── start.sh           # Render deployment start script
└── frontend/
    └── src/
        ├── components/
        │   ├── Home.jsx           # Landing page + hero section
        │   ├── WorkflowEditor.jsx # Step builder with branch management
        │   ├── RunViewer.jsx      # Real-time execution timeline view
        │   ├── History.jsx        # Past runs list with delete support
        │   ├── Layout.jsx         # App shell — nav, theme toggle, routing
        │   ├── NamingModal.jsx    # Workflow naming dialog
        │   └── ThemeToggle.jsx    # Light/Dark mode switcher
        ├── lib/
        │   ├── supabaseClient.js  # Supabase JS client for realtime
        │   └── utils.js           # Utility helpers (cn)
        └── App.jsx                # React Router setup
```

---

## 📄 License & Author

MIT License © 2026

**D Nivethitha** — [LinkedIn](https://www.linkedin.com/in/nivethitha-d-306a46326/) · [GitHub](https://github.com/nivethitha-code) · nivethithadharmarajan25@gmail.com
