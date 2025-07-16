import os
import csv

def save_message_to_user_file(username, session_id, timestamp, role, content, base_dir="data_persistence/user_chats"):
    os.makedirs(base_dir, exist_ok=True)
    filename = os.path.join(base_dir, f"{username}_chats.csv")
    file_exists = os.path.isfile(filename)
    with open(filename, "a", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["session_id", "timestamp", "role", "content"])  # header
        writer.writerow([session_id, timestamp, role, content]) 