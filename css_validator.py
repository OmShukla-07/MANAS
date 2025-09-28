#!/usr/bin/env python3
"""
CSS validator for learn_more.html template
"""

def validate_css_in_template(file_path):
    """Find CSS syntax issues in HTML template"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    
    in_style = False
    brace_stack = []
    
    for line_num, line in enumerate(lines, 1):
        if '<style>' in line:
            in_style = True
            print(f"Started CSS section at line {line_num}")
            continue
            
        if '</style>' in line:
            if brace_stack:
                print(f"❌ ERROR: Unclosed CSS rules at line {line_num}")
                print(f"Remaining open braces: {len(brace_stack)}")
                for i, brace_line in enumerate(brace_stack[-5:]):  # Show last 5
                    print(f"  Line {brace_line}: Unclosed brace")
                return False
            else:
                print(f"✅ CSS section ended properly at line {line_num}")
            in_style = False
            break
            
        if in_style:
            # Count braces in this line
            open_braces = line.count('{')
            close_braces = line.count('}')
            
            # Add open braces to stack
            for _ in range(open_braces):
                brace_stack.append(line_num)
                
            # Remove closed braces from stack
            for _ in range(close_braces):
                if brace_stack:
                    brace_stack.pop()
                else:
                    print(f"❌ ERROR at line {line_num}: Extra closing brace")
                    print(f"Line content: {line.strip()}")
                    return False
    
    if in_style and brace_stack:
        print(f"❌ ERROR: CSS section not properly closed")
        print(f"Unclosed braces: {len(brace_stack)}")
        return False
        
    print("✅ CSS validation passed")
    return True

if __name__ == "__main__":
    result = validate_css_in_template("templates/learn_more.html")
    if not result:
        exit(1)