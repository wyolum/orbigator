def check_version():
    try:
        with open("orb_utils.py", "r") as f:
            lines = f.readlines()
            
        print("--- orb_utils.py Check ---")
        found_debug = False
        for i, line in enumerate(lines):
            if "def save_state():" in line:
                print(f"Line {i}: {line.strip()}")
                # Print next 5 lines
                for j in range(1, 6):
                    if i+j < len(lines):
                        print(f"Line {i+j}: {lines[i+j].strip()}")
                        if "DEBUG: Saving state" in lines[i+j]:
                            found_debug = True
        
        if found_debug:
            print("\nRESULT: orb_utils.py is UPDATED (Debug prints found).")
        else:
            print("\nRESULT: orb_utils.py is STALE (No debug prints).")
            
    except Exception as e:
        print(f"Error reading file: {e}")

if __name__ == "__main__":
    check_version()
