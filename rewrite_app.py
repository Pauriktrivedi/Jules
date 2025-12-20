import os

with open('app.py', 'r') as f:
    lines = f.readlines()

split_line_index = -1
for i, line in enumerate(lines):
    if line.strip() == "# ---------- Load & preprocess ----------":
        split_line_index = i
        break

if split_line_index == -1:
    print("Could not find split point")
    exit(1)

new_lines = lines[:split_line_index]
new_lines.append("def main():\n")

for line in lines[split_line_index:]:
    new_lines.append("    " + line)

new_lines.append("\nif __name__ == \"__main__\":\n")
new_lines.append("    try:\n")
new_lines.append("        main()\n")
new_lines.append("    except Exception as e:\n")
new_lines.append("        st.error(\"An error occurred during application execution:\")\n")
new_lines.append("        st.text(traceback.format_exc())\n")

with open('app.py', 'w') as f:
    f.writelines(new_lines)

print("Successfully rewrote app.py")
