import os
import base64
import time
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder='.')
CORS(app)

client = None
try:
    from google import genai
    from google.genai import types
    API_KEY = "AQ.Ab8RN6KiAWOlfe5AvhLYfDrFxeBl75CdwT8jkOHAqjdSJtsZqw"
    client = genai.Client(api_key=API_KEY)
except Exception as e:
    print("Gemini API Init Note:", e)

BT = chr(96) * 3

LOCAL_KNOWLEDGE = {
    "beginner": f"""### Top 10 Essential Linux Commands for Beginners

1. **pwd** (Print Working Directory): Shows current path.
{BT}bash
pwd
{BT}

2. **ls** (List Files): Lists files and hidden items.
{BT}bash
ls -la
{BT}

3. **cd** (Change Directory): Switch folder.
{BT}bash
cd /var/log
{BT}

4. **mkdir** (Make Directory): Creates folder.
{BT}bash
mkdir my_project
{BT}

5. **touch** (Create File): Creates empty text file.
{BT}bash
touch notes.txt
{BT}

6. **cp** (Copy): Copies files or directories.
{BT}bash
cp file1.txt backup.txt
{BT}

7. **mv** (Move / Rename): Renames file.
{BT}bash
mv old.txt new.txt
{BT}

8. **rm** (Remove): Deletes safely.
{BT}bash
rm -r test_folder
{BT}

9. **cat** (View File): Shows file content.
{BT}bash
cat notes.txt
{BT}

10. **chmod** (Change Permissions):
{BT}bash
chmod +x script.sh
{BT}
""",
    "delete_folder": f"""### Permanently Delete Files and Folders in Linux

**Warning:** Linux lo delete chesina files Trash loki vellavu, direct ga permanently remove avthayi.

1. **Delete an empty directory:**
{BT}bash
rmdir folder_name
{BT}

2. **Forcefully and recursively delete a folder with all files (Destructive):**
{BT}bash
rm -rf /path/to/folder_name
{BT}

3. **Interactive deletion (Asks confirmation for safety):**
{BT}bash
rm -ri folder_name
{BT}
""",
    "diagnostics": f"""### Terminal Diagnostics & System Monitoring Commands

1. **CPU & Process Load:**
{BT}bash
top
{BT}

2. **RAM Memory Usage:**
{BT}bash
free -h
{BT}

3. **Disk Space Analysis:**
{BT}bash
df -h
{BT}

4. **Directory Storage Consumption:**
{BT}bash
du -sh * | sort -h
{BT}

5. **Open Network Ports:**
{BT}bash
ss -tulpn
{BT}
""",
    "scripting": f"""### Shell Scripting Basics (Bash Automation)

1. Create a script file:
{BT}bash
nano backup.sh
{BT}

2. Script content:
{BT}bash
#!/bin/bash
echo "Starting Backup..."
tar -czf backup_$(date +%F).tar.gz /home/$USER/Documents
echo "Backup Completed Successfully!"
{BT}

3. Give permission and run:
{BT}bash
chmod +x backup.sh
./backup.sh
{BT}
""",
    "software": f"""### Software Installation & Package Management (APT / DNF)

1. **Update package lists:**
{BT}bash
sudo apt update
{BT}

2. **Install new package:**
{BT}bash
sudo apt install nginx git python3 -y
{BT}

3. **Remove software:**
{BT}bash
sudo apt remove nginx
{BT}

4. **Clean residual cache files:**
{BT}bash
sudo apt autoremove -y && sudo apt clean
{BT}
""",
    "permissions": f"""### Linux File Permissions (chmod & chown)

1. **chmod 755 (Standard safe permission):**
{BT}bash
chmod 755 script.sh
{BT}

2. **chmod 777 (Full public access - Warning: Not safe for production):**
{BT}bash
chmod 777 test_folder
{BT}

3. **Change ownership to user:**
{BT}bash
sudo chown -R $USER:$USER /var/www/html
{BT}
""",
    "troubleshoot": f"""### Common Linux Terminal Errors & Troubleshooting

1. **Permission denied error fix:**
{BT}bash
chmod +x script.sh
{BT}

2. **Port already in use error fix:**
{BT}bash
sudo fuser -k 8080/tcp
{BT}

3. **Clean disk space when full:**
{BT}bash
sudo apt clean && sudo journalctl --vacuum-size=100M
{BT}
"""
}

LINUX_SYSTEM_INSTRUCTION = """
You are 'AI Linux Help Chatbot', an expert Linux Systems Administrator.
1. Provide clear bash commands inside markdown code blocks.
2. Explain flags clearly and suggest safe execution steps.
3. Keep terminal commands strictly in English.
"""

@app.route('/')
def home():
    return send_from_directory('.', 'index.html')

@app.route('/api/chat', methods=['POST'])
def linux_chat_endpoint():
    data = request.get_json(force=True)
    user_query = data.get("message", "").strip()
    file_b64 = data.get("file_base64", None)
    mime_type = data.get("mime_type", None)

    if not user_query and not file_b64:
        return jsonify({"reply": "Please enter a Linux question or terminal command inquiry."})

    q = user_query.lower()

    if not file_b64:
        if any(k in q for k in ["delete", "remove folder", "permanently", "rm -rf", "delete folder"]):
            return jsonify({"reply": LOCAL_KNOWLEDGE["delete_folder"]})
        if any(k in q for k in ["beginner", "top 10", "essential"]):
            return jsonify({"reply": LOCAL_KNOWLEDGE["beginner"]})
        if any(k in q for k in ["diagnostic", "memory usage", "cpu", "ram"]):
            return jsonify({"reply": LOCAL_KNOWLEDGE["diagnostics"]})
        if any(k in q for k in ["shell script", "bash script", "scripting"]):
            return jsonify({"reply": LOCAL_KNOWLEDGE["scripting"]})
        if any(k in q for k in ["software", "package", "install", "apt", "manage"]):
            return jsonify({"reply": LOCAL_KNOWLEDGE["software"]})
        if any(k in q for k in ["permission", "chmod", "chown", "777", "755"]):
            return jsonify({"reply": LOCAL_KNOWLEDGE["permissions"]})
        if any(k in q for k in ["error", "troubleshoot", "debug", "solve", "fix"]):
            return jsonify({"reply": LOCAL_KNOWLEDGE["troubleshoot"]})

    if client:
        try:
            contents = []
            if file_b64 and mime_type:
                img_bytes = base64.b64decode(file_b64)
                contents.append(types.Part.from_bytes(data=img_bytes, mime_type=mime_type))
            if user_query:
                contents.append(user_query)
            else:
                contents.append("Analyze this attached terminal or code screenshot and provide clear instructions.")

            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=contents,
                config={"system_instruction": LINUX_SYSTEM_INSTRUCTION}
            )
            if response and response.text:
                return jsonify({"reply": response.text})
        except Exception as e:
            print("API Exception:", e)

    return jsonify({"reply": f"{BT}bash\nman {user_query.split()[0]}\n{BT}\nTip: Adagandi - delete folder, beginner commands, permissions, diagnostics leda software installation."})

if __name__ == '__main__':
    print("\nAI Linux Help Chatbot Backend Running at: http://127.0.0.1:5002\n")
    app.run(host='127.0.0.1', port=5002, debug=False)