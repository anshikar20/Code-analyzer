# Omni Analyzer - Demo Python File for Testing Rules

# 1. Dependency Vulnerability Rule (Triggers a Security Error)
# Import requests or log4j which are flagged in DependencyRules.ts
import requests

# 2. Hardcoded Secret Rule (Triggers a Security Warning)
# Assigns a secret string of at least 10 characters
api_key = "my-secret-key-value-123"
passcode =  "1234007hi@"

# 3. Unused Variable Rule (Triggers an Unused Variable Warning)
# Variable assigned but never read (does not start with "_")
temp_unused_data = 100

# 4. Inefficient Loop Rule (Triggers a Performance Info alert)
# Defining a function inside a loop
for i in range(10):
    def compute_value():
        return i * 2

# 5. Syntax Error Rule (Triggers a Syntax Error)
# Uncomment the line below to test local incremental syntax error detection:
# if True
