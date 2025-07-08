import os
import sqlite3
from openai import OpenAI
import json

# Set your OpenAI API key here

client = OpenAI(
    api_key=os.environ.get("OpenAiKey"),  # This is the default and can be omitted
)

# --- Step 1: Create and Populate the SQLite Database with Sample Data ---
DB_FILE = "database.sqlite"

def create_database(db_file: str):
    """Create database and sample tables if not exist."""
    if os.path.exists(db_file):
        print(f"Database '{db_file}' already exists. Skipping creation.")
        return

    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    # Create sample table: employees
    cursor.execute("""
    CREATE TABLE employees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        age INTEGER,
        department_id INTEGER
    );
    """)

    # Create sample table: departments
    cursor.execute("""
    CREATE TABLE departments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL
    );
    """)

    # Insert sample data into departments
    departments = [
        ("Human Resources",),
        ("Engineering",),
        ("Sales",),
        ("Marketing",)
    ]
    cursor.executemany("INSERT INTO departments (name) VALUES (?);", departments)

    # Insert sample data into employees
    employees = [
        ("Alice", 30, 2),
        ("Bob", 45, 3),
        ("Charlie", 25, 2),
        ("Diana", 35, 1),
        ("Eve", 40, 4),
        ("Frank", 50, 3)
    ]
    cursor.executemany("INSERT INTO employees (name, age, department_id) VALUES (?, ?, ?);", employees)

    conn.commit()
    conn.close()
    print(f"Database '{db_file}' created and populated with sample data.")

# --- Step 2: OpenAI Prompts for SQL and Chart Configurations ---

TEXT2SQL_PROMPT = """
## Description
You are a data engineer responsible for translating management requirements into SQL statements that can be executed in SQLite.
You are provided with table schemas in the following format:
{database_schema}

If the requirement exceeds the provided schema info, return "BeyondError".

## Examples
Requirement: Find the name and age of the oldest employee.
SQL: SELECT name, age FROM employees ORDER BY age DESC LIMIT 1;

Requirement: Who is my best friend?
SQL: BeyondError

## Task to solve
Requirement: {requirement}
SQL:
"""

DATA2CHART_PROMPT = """
## Description
You are a JS engineer proficient in ECharts. You are provided with a requirement and SQL result.
Based on the following rules, generate a valid ECharts option configuration (in JSON format) without extra comments:
1. If there's only one data point, use a gauge chart.
2. If the requirement involves proportions, use a pie chart.
3. If data is one-dimensional with <=6 data points, use a radar chart.
4. Otherwise, use line, scatter, or multi-series bar chart as appropriate.
All numeric values must have at most two decimal places.
Return "ChartError" if data is empty or improperly formatted.

Requirement: {requirement}
SQL Result: {result}
Result:
"""

def ask_openai(prompt: str) -> str:
    """Call OpenAI's API with the given prompt and return the response text."""
    chat_completion = client.chat.completions.create(
        model="gpt-4o",  # Adjust model if needed.
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    return chat_completion.choices[0].message.content.strip()


# --- Step 3: Define Classes for Text2SQL and Data2Chart ---

class Text2SQL:
    def __init__(self, database_schema: str):
        self.database_schema = database_schema

    def gen_sql(self, requirement: str) -> str:
        prompt = TEXT2SQL_PROMPT.format(
            database_schema=self.database_schema,
            requirement=requirement
        )
        sql = ask_openai(prompt)
        if sql == "BeyondError":
            print(f"Error: Requirement exceeds provided schema for [{requirement}]")
        return sql

class Data2Chart:
    def __init__(self):
        pass

    def gen_chart(self, requirement: str, result: list) -> str:
        result_str = json.dumps(result)
        prompt = DATA2CHART_PROMPT.format(requirement=requirement, result=result_str)
        return ask_openai(prompt)

# --- Step 4: Helper Functions to Fetch Data and Retrieve Schema ---

def fetch_data(sql: str, db_file: str = DB_FILE) -> list:
    """Execute the SQL query against the SQLite database and return the data."""
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        cursor.execute(sql)
        data = cursor.fetchall()
        # Retrieve column names from the cursor
        columns = [desc[0] for desc in cursor.description]
        conn.close()
        return [columns] + data
    except Exception as e:
        print(f"Error executing SQL: {e}")
        return []

def get_database_schema(db_file: str = DB_FILE) -> str:
    """
    Retrieve basic schema information from the SQLite database.
    For each table, list its name and column details.
    """
    schema_info = []
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    for (table_name,) in tables:
        cursor.execute(f"PRAGMA table_info('{table_name}');")
        columns = cursor.fetchall()
        col_info = "\n".join(
            [f"col:{col[1]}, type:{col[2]}" for col in columns]
        )
        schema_info.append(f"table: {table_name}\ncolumns:\n{col_info}")
    conn.close()
    return "\n\n".join(schema_info)

# --- Main Script ---

if __name__ == '__main__':
    # Step A: Create and populate database if necessary.
    create_database(DB_FILE)

    # Step B: Retrieve database schema.
    database_schema = get_database_schema()
    print("Database Schema:")
    print(database_schema)
    print("\n" + "="*50 + "\n")

    # Step C: Get user requirement.
    requirement = input("Enter your requirement: ").strip()

    # Step D: Generate SQL from requirement.
    text2sql = Text2SQL(database_schema)
    sql = text2sql.gen_sql(requirement)
    print(f"\nGenerated SQL:\n{sql}\n")
    
    if sql == "BeyondError":
        exit(1)

    # Step E: Execute SQL and fetch data.
    result = fetch_data(sql)
    if not result or len(result) < 2:
        print("ChartError: No or insufficient data returned from SQL.")
        exit(1)
    print("Fetched Data:")
    print(result)
    print("\n" + "="*50 + "\n")
    
    # Step F: Generate ECharts configuration from requirement and SQL result.
    data2chart = Data2Chart()
    chart_config = data2chart.gen_chart(requirement, result)
    print("ECharts Option Configuration:")
    print(chart_config)
