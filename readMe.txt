````markdown
# Text2SQL & Data2Chart

Convert natural-language requirements into SQLite queries and ECharts configs via OpenAI.

## Prerequisites

- Python 3.7+
- SQLite
- OpenAI API key

## Installation

```bash
git clone https://github.com/1hm544i5f1ll1/SQLightChart.git
cd SQLightChart.git
pip install openai sqlite3
````

## Configuration

Set your API key in env:

```bash
export OpenAiKey="your-openai-key"
```

## Usage

```bash
python script.py
```

1. Creates `database.sqlite` with sample tables (`employees`, `departments`).
2. Prints DB schema.
3. Prompts for a requirement (e.g. “Find oldest employee”).
4. Generates SQL via OpenAI.
5. Executes SQL and shows results.
6. Generates ECharts JSON config via OpenAI.

## Files

* `script.py` — main script
* `database.sqlite` — auto-created sample DB

## Key Classes & Functions

* `create_database()` — init & seed DB
* `get_database_schema()` — retrieve table/column info
* `Text2SQL.gen_sql()` — prompt→SQL
* `fetch_data()` — run SQL, return rows
* `Data2Chart.gen_chart()` — prompt→ECharts JSON
 
