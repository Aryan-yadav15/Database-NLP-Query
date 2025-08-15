"""
LLM Prompt Engineering Templates Module
=======================================

This module contains all engineered prompts used throughout the Brain LLM application
for various Large Language Model interactions. Centralizing prompts enables consistent
AI behavior, easy maintenance, version control, and A/B testing of prompt effectiveness.

Key Features:
- Centralized prompt management for consistency across services
- Template-based prompts with variable substitution
- Domain-specific prompts optimized for different use cases
- Version control and collaborative prompt engineering
- Performance optimization through prompt structure

Prompt Categories:
1. Query Routing: Intelligent decision-making for query classification
2. SQL Generation: Natural language to SQL conversion with safety constraints
3. Data Quality: Rule discovery and validation prompt templates
4. Visualization: Graph generation and schema visualization prompts
5. Result Formatting: Response structuring and user communication

Design Principles:
- Clear instructions with specific output formats
- Context-aware prompts with relevant schema information
- Safety constraints to prevent harmful or incorrect operations
- Few-shot examples for improved accuracy
- Structured output formats for downstream processing

Prompt Engineering Best Practices:
- Specific, unambiguous instructions
- Clear output format specifications
- Relevant context and constraints
- Error handling and edge case coverage
- Performance optimization for token efficiency

Author: Brain LLM Team
"""


# =============================================================================
# DATABASE SCHEMA DEFINITIONS
# =============================================================================

ADVENTUREWORKS_SCHEMA = """
Key tables and their relationships in the AdventureWorks sample database:

Core Business Entities:
- Product (ProductID, Name, ProductNumber, ListPrice, Color)
- SalesOrderHeader (SalesOrderID, OrderDate, CustomerID, TotalDue)
- SalesOrderDetail (SalesOrderID, ProductID, OrderQty, UnitPrice)
- Customer (CustomerID, PersonID, StoreID)
- Person (BusinessEntityID/PersonID, FirstName, LastName, EmailAddress)

This simplified schema provides essential table structures for basic query examples
and documentation. The full schema is dynamically loaded from the database.
"""

# Placeholder for dynamic schema - populated at runtime from database introspection
ADVENTUREWORKS_SCHEMA_FOR_LLM = """
Dynamic database schema populated at application startup.
See sql_query_router_logic.py for schema extraction implementation.
"""


# =============================================================================
# QUERY ROUTING PROMPTS
# =============================================================================

DECIDE_QUERY_PATH_PROMPT_TEMPLATE = """You are an intelligent query routing agent for the AdventureWorks database.
Your task is to analyze the user's query and decide the most appropriate processing strategy:

**ROUTING OPTIONS:**
1. **SQL Route**: For precise data queries, calculations, and database metadata
2. **Data Quality (DQ) Route**: For data validation rules, quality checks, and constraints
3. **Visualization Route**: For database schema visualization and relationship diagrams

**DATABASE SCHEMA:**
{schema_to_use_in_prompt}

**ROUTING DECISION MATRIX:**

**Choose "ROUTE: SQL" when the query:**
- Requests specific data calculations (counts, sums, averages, min/max values)
- Asks for data lists based on precise conditions (numeric, date, string equality)
- Inquires about database metadata (table lists, column definitions, schema info)
- Seeks information likely stored in structured database fields
- Requires data retrieval or reporting functionality

**Choose "ROUTE: DQ" when the query:**
- Discusses data quality rules, validation criteria, or business constraints
- Asks about data consistency, completeness, or accuracy requirements
- Inquires about data validation processes or quality metrics
- Focuses on data governance, compliance, or quality standards

**Choose "ROUTE: VISUALIZE" when the query:**
- Requests database structure visualization or entity relationship diagrams
- Asks about table relationships, schema connections, or data model visualization
- Seeks graphical representation of database architecture

**USER QUERY:** "{user_query}"

**INSTRUCTIONS:**
Analyze the query carefully and respond with EXACTLY one of these three options:
- "ROUTE: SQL"
- "ROUTE: DQ" 
- "ROUTE: VISUALIZE"

Do not include any additional text, explanations, or formatting. Your response must be precisely one of the three routing options listed above.
"""


# =============================================================================
# SQL GENERATION PROMPTS
# =============================================================================

GENERATE_SQL_PROMPT_TEMPLATE = """You are an expert PostgreSQL query writer specializing in the AdventureWorks database.
Your mission is to convert natural language questions into syntactically correct, efficient PostgreSQL queries.

**CRITICAL SCHEMA COMPLIANCE RULES:**

1. **STRICT SCHEMA ADHERENCE:** 
   - Use ONLY the exact table and column names from the provided schema
   - Never invent or assume column names not explicitly listed
   - Respect schema prefixes (e.g., sales.customer, production.product)

2. **QUERY SAFETY AND BEST PRACTICES:**
2.  **IMPLIED CALCULATIONS:** If a user asks for a value that requires a calculation (like "total sales"), you MUST derive it from the available columns (e.g., `SUM("unitprice" * "orderqty")`).
3.  **SCHEMA AWARENESS:** The database has multiple important schemas (e.g., `production`, `sales`, `person`). If a user asks to "list all tables", you MUST query `information_schema.tables` and include a `WHERE table_schema IN (...)` clause with the relevant application schemas. **DO NOT assume the schema is 'public'.**
4.  **QUOTING:** ALWAYS enclose schema, table, and column names in double quotes.
5.  **READ-ONLY:** Only generate SELECT statements.
---
Database Schema:
{detailed_schema_str}
---
User Question: "{user_query}"
---

PostgreSQL Query (Strictly following all rules, especially lowercase and quoting):"""

# Format SQL Results Prompt
FORMAT_SQL_RESULTS_PROMPT_TEMPLATE = """
TASK: You are an expert at presenting data to users. Given a user's question and the raw data from a SQL query, your job is to generate a structured JSON response.

USER'S QUESTION:
"{user_query}"

RAW DATA (in Markdown format):
{results_str}

JSON OUTPUT REQUIREMENTS:
1.  Your entire response MUST be a single, raw JSON object. Do not add any commentary.
2.  The JSON object must have two keys: "answer_text" and "table_data".
3.  "answer_text": A short, friendly, one-sentence summary that introduces the data.
4.  "table_data": A JSON object with "title", "columns", and "rows" keys.
    - "title": A concise, descriptive title for the table.
    - "columns": An array of strings with the column names.
    - "rows": An array of arrays, with each inner array representing a data row.

EXAMPLE:
{{
  "answer_text": "Here is the list of top selling product subcategories you requested.",
  "table_data": {{
    "title": "Top Selling Product Subcategories",
    "columns": ["product_subcategory", "total_quantity_ordered"],
    "rows": [
      ["Road Bikes", 47196],
      ["Mountain Bikes", 28321]
    ]
  }}
}}

Begin the JSON response now.
"""

# Entity Extraction Prompt
EXTRACT_ENTITIES_PROMPT_TEMPLATE = """You are a database entity extractor. Your job is to read a user's query and a list of available tables, then identify which tables the user is most likely interested in.

User's Query: "{user_query}"

Available Tables (schema.table format):
{schema_summary}

From the "Available Tables", identify the tables that are most relevant to the "User's Query".
List the relevant table names in a simple comma-separated format.
- If the query is specific (e.g., "show me product information", "relations for customer and orders"), return the relevant table names (e.g., `production.product`, `sales.customer,sales.salesorderheader`).
- If the query is generic (e.g., "visualize the database", "show me the schema"), do not return any table names, just an empty string.
- Only return table names that exist in the "Available Tables" list.
- Return the fully-qualified table names.

Respond ONLY with the comma-separated list of fully-qualified table names or an empty string. Do not add any other text.
"""

# DQ Rule SQL Generation Prompt
GENERATE_DQ_SQL_PROMPT_TEMPLATE = """
Given the following Data Quality Rule Description and the Database Schema:

Rule Description:
"{rule_description}"

Database Schema:
{detailed_schema_str}

Your tasks are:
1. Identify the primary database TABLE this rule most likely applies to. If multiple, pick the most central one.
2. Identify the primary database COLUMN(s) this rule most likely applies to within that table.
3. Generate a PostgreSQL SQL query that could be used to find data rows that violate or are relevant to this rule. The query should select relevant columns and filter based on the rule.

Provide your response strictly as a JSON object with the following keys:
- "table": (string) The name of the database table (e.g., "Customer" or "Sales.OrderHeader"). Use schema qualification if appropriate and present in the provided schema context.
- "columns": (list of strings) The names of the relevant columns (e.g., ["PostalCode", "Country"]).
- "sql_query": (string) The PostgreSQL SQL query.

If you cannot confidently determine any piece of information, use null for its value for that key within the JSON structure.
Ensure the output is ONLY the JSON object, with no other text or explanations before or after it.

Example based on a hypothetical schema:
Rule Description: "Percentage of Customers with blank Postal Code(Zip code)"
Database Schema (excerpt):
CREATE TABLE Customer (CustomerID INT PRIMARY KEY, FirstName VARCHAR(50), PostalCode VARCHAR(10));
CREATE TABLE Sales.Orders (OrderID INT, CustomerID INT, OrderDate DATE);

Expected JSON Output:
{{
  "table": "Customer",
  "columns": ["PostalCode"],
  "sql_query": "SELECT CustomerID, PostalCode FROM Customer WHERE PostalCode IS NULL OR PostalCode = '';"
}}
"""

# Visualization JSON Generation Prompt
GENERATE_VISUALIZATION_JSON_PROMPT_TEMPLATE = """
TASK: Convert the provided database schema into a JSON object for a TABLE-LEVEL graph visualization. Your main goal is to show how tables are related to each other.
 
INPUT SCHEMA:
---
{focused_schema_str}
---
 
USER'S FOCUS:
---
"{user_query}"
---
 
JSON OUTPUT REQUIREMENTS:
1.  The entire response MUST be a single, raw JSON object. Do not wrap it in markdown or add commentary.
2.  The root object must have a SINGLE key: "graph", which contains "nodes" and "edges".
3.  "nodes": Create a node for each TABLE only. Do NOT create nodes for individual columns.
    - Node properties: "id" (fully qualified table name), "label" (short table name), "group" ('table').
4.  "edges": Create an edge for each FOREIGN KEY relationship. The edge must connect the two parent TABLES involved.
    - Edge properties: "from", "to", "label".
    - **Edge Labeling Rule:** Analyze the source and target TABLE names to infer a concise, human-readable verb phrase that describes the business relationship. The label should be lowercase. For example, if 'sales.salesorderheader' links to 'sales.customer', a good label is 'placed by'.
 
EXAMPLE OF THE FINAL STRUCTURE:
{{
  "graph": {{
    "nodes": [
      {{
        "id": "sales.salesorderheader",
        "label": "salesorderheader",
        "group": "table"
      }},
      {{
        "id": "sales.customer",
        "label": "customer",
        "group": "table"
      }},
      {{
        "id": "production.product",
        "label": "product",
        "group": "table"
      }}
    ],
    "edges": [
      {{
        "from": "sales.salesorderheader",
        "to": "sales.customer",
        "label": "placed by"
      }},
      {{
        "from": "sales.salesorderheader",
        "to": "production.product",
        "label": "contains"
      }}
    ]
  }}
}}
 
Begin the JSON response now.
"""
