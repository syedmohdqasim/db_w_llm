import google.generativeai as genai
import os
import re

class LLMAdapter:
    def __init__(self, api_key):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')

    def translate_to_sql(self, question, schema):
        prompt = f"""
        You are a SQL expert. Given the following SQLite database schema, 
        write a SQL query that answers the user's question.
        
        Schema:
        {schema}
        
        Question:
        {question}
        
        Return ONLY the SQL query. Do not include markdown formatting, backticks, or any explanation.
        """
        
        response = self.model.generate_content(prompt)
        sql = response.text.strip()
        
        # Clean up any potential markdown formatting if Gemini includes it despite instructions
        sql = re.sub(r'```sql\n?', '', sql)
        sql = re.sub(r'```', '', sql)
        
        return sql.strip()

if __name__ == "__main__":
    # Mock for testing if no key is provided
    import sys
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        print("GEMINI_API_KEY not found in environment")
        sys.exit(1)
        
    adapter = LLMAdapter(key)
    test_schema = "CREATE TABLE users (id INTEGER, name TEXT, age INTEGER);"
    test_question = "How many users are older than 25?"
    print(f"SQL: {adapter.translate_to_sql(test_question, test_schema)}")
