#!/usr/bin/env python3

import sys
sys.path.append('.')

from tools.cli import scaffold

# Test scaffolding directly
if __name__ == "__main__":
    try:
        scaffold(
            resource="book",
            endpoint_path="/books", 
            methods="GET,POST",
            fields="title:str,pages:int"
        )
        print("Scaffold completed successfully!")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()