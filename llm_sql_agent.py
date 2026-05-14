# llm_sql_agent.py
import sqlite3
from sqlalchemy import create_engine

from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent
from langchain_openai import ChatOpenAI  # OpenAI-compatible interface

import config_local

# dataset moved out
from employee_dataset import DB_PATH, EMPLOYEE_ROWS


def init_db():
    """Create/reset the SQLite DB and seed it with EMPLOYEE_ROWS."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS employees (
            name   TEXT NOT NULL,
            dept   TEXT NOT NULL,
            title  TEXT NOT NULL,
            salary INTEGER NOT NULL
        )
        """
    )

    # Reset table
    cur.execute("DELETE FROM employees")

    # Seed rows
    cur.executemany(
        "INSERT INTO employees (name, dept, title, salary) VALUES (?, ?, ?, ?)",
        EMPLOYEE_ROWS,
    )

    conn.commit()
    conn.close()


def build_agent(verbose: bool = False):
    """Build a LangChain SQL agent powered by DeepSeek (OpenAI-compatible API)."""
    # Connect to database
    engine = create_engine(f"sqlite:///{DB_PATH}")
    db = SQLDatabase(engine)

    # LLM (OpenAI-compatible)
    llm = ChatOpenAI(
        model=config_local.LLM_MODEL,  # e.g. "deepseek-chat" or "qwen-plus"
        temperature=0,
        api_key=config_local.LLM_API_KEY,
        base_url=config_local.LLM_BASE_URL,
    )

    # Create SQL Agent
    agent = create_sql_agent(
        llm=llm,
        db=db,
        verbose=verbose,
        agent_type="tool-calling",
    )
    return agent


def main():
    init_db()
    agent = build_agent(verbose=True)

    print("LLM SQL Agent ready. Type your question, or 'exit' to quit.\n")
    print("Examples:")
    print(" - What is the average salary in Engineering?")
    print(" - Who earns the highest salary?")
    print(" - List employees with salary > 25000 ordered by salary descending.\n")

    while True:
        q = input("You> ").strip()
        if q.lower() in {"exit", "quit"}:
            break

        out = agent.invoke({"input": q})
        print("\nAnswer>\n", out.get("output", out), "\n")


if __name__ == "__main__":
    main()