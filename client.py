# NOTICE: despite what the AGPL Version 3 license states, you are NOT PERMITTED to make this your own project in any case, you may create a github fork, but regular new projects are FORBIDDEN
import tkinter as tk
from tkinter.scrolledtext import ScrolledText
from tkinter import messagebox, simpledialog
import requests
import threading
import time
import json
import os

SERVER = "https://messenger.theuselesssite.org"
HEADERS = {"Content-Type": "application/json"}
username = None
my_code = None
last_timestamp = 0

SETTINGS_FILE = os.path.join(os.path.dirname(__file__), "settings.json")

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {"dark_mode": False, "speed_dial": [], "show_speed_dial": False}

def save_settings(settings):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=2)

LIGHT = {
    "bg": "#f0f0f0",
    "fg": "#000000",
    "entry_bg": "#ffffff",
    "chat_bg": "#ffffff",
    "btn_bg": "#e0e0e0",
    "btn_fg": "#000000",
}
DARK = {
    "bg": "#2b2b2b",
    "fg": "#e0e0e0",
    "entry_bg": "#3c3c3c",
    "chat_bg": "#1e1e1e",
    "btn_bg": "#444444",
    "btn_fg": "#e0e0e0",
}

def chat_ui():
    global last_timestamp, username, my_code
    settings = load_settings()

    win = tk.Tk()
    win.title(f"Messenger - {username}")
    win.geometry("450x600")

    def theme():
        return DARK if settings["dark_mode"] else LIGHT

    def apply_theme():
        t = theme()
        win.config(bg=t["bg"])
        chat.config(bg=t["chat_bg"], fg=t["fg"], insertbackground=t["fg"])
        to_e.config(bg=t["entry_bg"], fg=t["fg"], insertbackground=t["fg"])
        msg_e.config(bg=t["entry_bg"], fg=t["fg"], insertbackground=t["fg"])
        send_btn.config(bg=t["btn_bg"], fg=t["btn_fg"])
        bottom_frame.config(bg=t["bg"])

    # --- Menu bar ---
    menubar = tk.Menu(win)

    # Settings menu
    settings_menu = tk.Menu(menubar, tearoff=0)
    dark_var = tk.BooleanVar(value=settings["dark_mode"])

    def toggle_dark_mode():
        settings["dark_mode"] = not settings["dark_mode"]
        dark_var.set(settings["dark_mode"])
        save_settings(settings)
        apply_theme()

    def change_username_dialog():
        global username
        pw = simpledialog.askstring("Change Username", "Current password:", show="*", parent=win)
        if not pw:
            return
        new = simpledialog.askstring("Change Username", "New username:", parent=win)
        if not new or not new.strip():
            return
        try:
            r = requests.post(SERVER + "/change_username", json={
                "username": username, "password": pw, "new_username": new.strip()
            }, headers=HEADERS).json()
            if "ok" in r:
                username = new.strip()
                win.title(f"Messenger - {username}")
                messagebox.showinfo("Success", "Username changed.", parent=win)
            else:
                messagebox.showerror("Error", r.get("error", "Failed"), parent=win)
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=win)

    def change_password_dialog():
        old_pw = simpledialog.askstring("Change Password", "Current password:", show="*", parent=win)
        if not old_pw:
            return
        new_pw = simpledialog.askstring("Change Password", "New password:", show="*", parent=win)
        if not new_pw:
            return
        try:
            r = requests.post(SERVER + "/change_password", json={
                "username": username, "password": old_pw, "new_password": new_pw
            }, headers=HEADERS).json()
            if "ok" in r:
                messagebox.showinfo("Success", "Password changed.", parent=win)
            else:
                messagebox.showerror("Error", r.get("error", "Failed"), parent=win)
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=win)

    def delete_account_dialog():
        if not messagebox.askyesno("Delete Account", "Are you sure? This cannot be undone.", parent=win):
            return
        pw = simpledialog.askstring("Delete Account", "Enter password to confirm:", show="*", parent=win)
        if not pw:
            return
        try:
            r = requests.post(SERVER + "/delete_account", json={
                "username": username, "password": pw
            }, headers=HEADERS).json()
            if "ok" in r:
                messagebox.showinfo("Deleted", "Account deleted. The app will now close.", parent=win)
                win.destroy()
            else:
                messagebox.showerror("Error", r.get("error", "Failed"), parent=win)
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=win)

    # friends_only_var = tk.BooleanVar()

    # def load_friends_only():
    #     try:
    #         r = requests.get(SERVER + f"/get_friends_only?username={username}").json()
    #         friends_only_var.set(r.get("enabled", False))
    #     except Exception:
    #         pass

    # def toggle_friends_only():
    #     pw = simpledialog.askstring("Friends Only", "Confirm password:", show="*", parent=win)
    #     if not pw:
    #         friends_only_var.set(not friends_only_var.get())
    #         return
    #     try:
    #         r = requests.post(SERVER + "/set_friends_only", json={
    #             "username": username, "password": pw, "enabled": friends_only_var.get()
    #         }, headers=HEADERS).json()
    #         if "ok" not in r:
    #             messagebox.showerror("Error", r.get("error", "Failed"), parent=win)
    #             friends_only_var.set(not friends_only_var.get())
    #     except Exception as e:
    #         messagebox.showerror("Error", str(e), parent=win)
    #         friends_only_var.set(not friends_only_var.get())

    speed_dial_var = tk.BooleanVar(value=settings.get("show_speed_dial", False))
    speed_dial_menu = tk.Menu(menubar, tearoff=0)

    def toggle_speed_dial():
        settings["show_speed_dial"] = speed_dial_var.get()
        save_settings(settings)
        if settings["show_speed_dial"]:
            menubar.insert_cascade(2, label="Speed Dial", menu=speed_dial_menu)
        else:
            try:
                menubar.delete("Speed Dial")
            except Exception:
                pass

    settings_menu.add_checkbutton(label="Dark Mode", command=toggle_dark_mode, variable=dark_var)
    settings_menu.add_checkbutton(label="Show Speed Dial", command=toggle_speed_dial, variable=speed_dial_var)
    # settings_menu.add_checkbutton(label="Friends Only Messaging", command=toggle_friends_only, variable=friends_only_var)
    settings_menu.add_separator()
    settings_menu.add_command(label="Change Username...", command=change_username_dialog)
    settings_menu.add_command(label="Change Password...", command=change_password_dialog)
    settings_menu.add_separator()
    settings_menu.add_command(label="Delete Account...", command=delete_account_dialog)
    menubar.add_cascade(label="Settings", menu=settings_menu)

    # load_friends_only()

    def refresh_speed_dial():
        speed_dial_menu.delete(0, "end")
        for contact in settings["speed_dial"]:
            speed_dial_menu.add_command(label=contact, command=lambda c=contact: set_recipient(c))
        speed_dial_menu.add_separator()
        speed_dial_menu.add_command(label="Add Contact...", command=add_speed_dial)
        speed_dial_menu.add_command(label="Remove Contact...", command=remove_speed_dial)

    def set_recipient(contact):
        to_e.delete(0, "end")
        to_e.insert(0, contact)

    def add_speed_dial():
        contact = simpledialog.askstring("Add Contact", "Enter username:", parent=win)
        if contact and contact.strip():
            contact = contact.strip()
            if contact not in settings["speed_dial"]:
                settings["speed_dial"].append(contact)
                save_settings(settings)
                refresh_speed_dial()

    def remove_speed_dial():
        if not settings["speed_dial"]:
            messagebox.showinfo("Speed Dial", "No contacts to remove.", parent=win)
            return
        contact = simpledialog.askstring(
            "Remove Contact",
            "Enter username to remove:\n" + "\n".join(settings["speed_dial"]),
            parent=win
        )
        if contact and contact.strip() in settings["speed_dial"]:
            settings["speed_dial"].remove(contact.strip())
            save_settings(settings)
            refresh_speed_dial()

    if settings.get("show_speed_dial", False):
        menubar.add_cascade(label="Speed Dial", menu=speed_dial_menu)

    # Friends menu
    friends_menu = tk.Menu(menubar, tearoff=0)
    friends_menu.add_command(label="Friends & Requests...", command=lambda: open_friends_window())
    menubar.add_cascade(label="Friends", menu=friends_menu)

    win.config(menu=menubar)
    refresh_speed_dial()

    # --- Chat area ---
    chat = ScrolledText(win, state="disabled")
    chat.pack(fill="both", expand=True)

    def add(msg):
        chat.config(state="normal")
        chat.insert("end", msg + "\n")
        chat.config(state="disabled")
        chat.see("end")

    to_e = tk.Entry(win)
    to_e.pack(fill="x")
    to_e.insert(0, "Recipient")

    msg_e = tk.Entry(win)
    msg_e.pack(fill="x")

    def send():
        try:
            msg = msg_e.get()
            if not msg:
                return
            r = requests.post(
                SERVER + "/send_message",
                json={"from": username, "to": to_e.get(), "msg": msg},
                headers=HEADERS
            ).json()
            if "ok" in r:
                add(f"You → {to_e.get()}: {msg}")
                msg_e.delete(0, "end")
            else:
                messagebox.showerror("Error", r.get("error", "Send failed"))
        except Exception as e:
            messagebox.showerror("Error", str(e))

    msg_e.bind("<Return>", lambda e: send())

    bottom_frame = tk.Frame(win)
    bottom_frame.pack(fill="x")
    send_btn = tk.Button(bottom_frame, text="Send", command=send)
    send_btn.pack(side="right")

    apply_theme()

    # --- Friends window ---
    def open_friends_window():
        fw = tk.Toplevel(win)
        fw.title("Friends")
        fw.geometry("360x500")
        fw.resizable(False, False)

        t = theme()
        fw.config(bg=t["bg"])

        def lbl(parent, text, **kw):
            return tk.Label(parent, text=text, bg=t["bg"], fg=t["fg"], **kw)

        def btn(parent, text, cmd):
            return tk.Button(parent, text=text, command=cmd, bg=t["btn_bg"], fg=t["btn_fg"])

        # Your code
        code_frame = tk.Frame(fw, bg=t["bg"])
        code_frame.pack(fill="x", padx=10, pady=(10, 4))
        lbl(code_frame, f"Your friend code:  {my_code}", font=("", 10, "bold")).pack(side="left")

        # Send request
        send_frame = tk.LabelFrame(fw, text="Send Friend Request", bg=t["bg"], fg=t["fg"])
        send_frame.pack(fill="x", padx=10, pady=4)
        code_entry = tk.Entry(send_frame, bg=t["entry_bg"], fg=t["fg"])
        code_entry.pack(side="left", fill="x", expand=True, padx=(4, 2), pady=4)

        def send_request():
            code = code_entry.get().strip()
            if not code:
                return
            try:
                r = requests.post(SERVER + "/send_friend_request", json={
                    "username": username, "code": code
                }, headers=HEADERS).json()
                if "ok" in r:
                    messagebox.showinfo("Sent", "Friend request sent!", parent=fw)
                    code_entry.delete(0, "end")
                else:
                    messagebox.showerror("Error", r.get("error", "Failed"), parent=fw)
            except Exception as e:
                messagebox.showerror("Error", str(e), parent=fw)

        btn(send_frame, "Send", send_request).pack(side="left", padx=(0, 4), pady=4)

        # Pending requests
        req_frame = tk.LabelFrame(fw, text="Pending Requests", bg=t["bg"], fg=t["fg"])
        req_frame.pack(fill="both", expand=True, padx=10, pady=4)
        req_inner = tk.Frame(req_frame, bg=t["bg"])
        req_inner.pack(fill="both", expand=True, padx=4, pady=4)

        # Friends list
        fl_frame = tk.LabelFrame(fw, text="Friends", bg=t["bg"], fg=t["fg"])
        fl_frame.pack(fill="both", expand=True, padx=10, pady=4)
        fl_inner = tk.Frame(fl_frame, bg=t["bg"])
        fl_inner.pack(fill="both", expand=True, padx=4, pady=4)

        def refresh():
            for w in req_inner.winfo_children():
                w.destroy()
            for w in fl_inner.winfo_children():
                w.destroy()
            try:
                reqs = requests.get(SERVER + f"/get_friend_requests?username={username}").json().get("requests", [])
                for req in reqs:
                    row = tk.Frame(req_inner, bg=t["bg"])
                    row.pack(fill="x", pady=1)
                    lbl(row, req["from"]).pack(side="left")

                    def accept(rid=req["id"]):
                        try:
                            r = requests.post(SERVER + "/accept_friend_request", json={
                                "username": username, "request_id": rid
                            }, headers=HEADERS).json()
                            if "ok" in r:
                                refresh()
                            else:
                                messagebox.showerror("Error", r.get("error", "Failed"), parent=fw)
                        except Exception as e:
                            messagebox.showerror("Error", str(e), parent=fw)

                    def decline(rid=req["id"]):
                        try:
                            r = requests.post(SERVER + "/decline_friend_request", json={
                                "username": username, "request_id": rid
                            }, headers=HEADERS).json()
                            if "ok" in r:
                                refresh()
                            else:
                                messagebox.showerror("Error", r.get("error", "Failed"), parent=fw)
                        except Exception as e:
                            messagebox.showerror("Error", str(e), parent=fw)

                    btn(row, "Accept", accept).pack(side="right", padx=2)
                    btn(row, "Decline", decline).pack(side="right")

                if not reqs:
                    lbl(req_inner, "No pending requests").pack()

                friends = requests.get(SERVER + f"/get_friends?username={username}").json().get("friends", [])
                for f in friends:
                    row = tk.Frame(fl_inner, bg=t["bg"])
                    row.pack(fill="x", pady=1)
                    lbl(row, f).pack(side="left")
                    btn(row, "Message", lambda name=f: (set_recipient(name), fw.focus_force(), msg_e.focus())).pack(side="right")

                if not friends:
                    lbl(fl_inner, "No friends yet").pack()

            except Exception as e:
                messagebox.showerror("Error", str(e), parent=fw)

        btn(fw, "Refresh", refresh).pack(pady=(0, 8))
        refresh()

    # --- Poll ---
    def poll():
        global last_timestamp
        while True:
            try:
                r = requests.get(
                    SERVER + f"/get_messages?username={username}&since={last_timestamp}"
                ).json()
                for msg in r["messages"]:
                    add(f"{msg['from']}: {msg['msg']}")
                    last_timestamp = max(last_timestamp, msg["timestamp"])
                time.sleep(2)
            except Exception:
                time.sleep(5)

    threading.Thread(target=poll, daemon=True).start()
    win.mainloop()


root = tk.Tk()
tk.Label(root, text="Username").pack()
user_e = tk.Entry(root)
user_e.pack()
tk.Label(root, text="Password").pack()
pwd_e = tk.Entry(root, show="*")
pwd_e.pack()

def register():
    try:
        attempted = user_e.get().strip()
        if attempted.lower() == "nigger":
            messagebox.showerror("Error", "really bro?")
            return
        r = requests.post(
            SERVER + "/register",
            json={"username": attempted, "password": pwd_e.get().strip()},
            headers=HEADERS
        )
        data = r.json()
        if "code" in data or "ok" in data:
            login()
        else:
            error = data.get("error", "Register failed")
            if attempted.lower() == "feather" and "taken" in error.lower():
                error = "nice try but we already have that one"
            messagebox.showerror("Error", error)
    except Exception as e:
        messagebox.showerror("Error", str(e))

def login():
    global username, my_code
    try:
        r = requests.post(
            SERVER + "/login",
            json={"username": user_e.get(), "password": pwd_e.get()},
            headers=HEADERS
        ).json()
        if "ok" in r:
            username = user_e.get()
            my_code = r.get("code", "??????")
            root.destroy()
            chat_ui()
        else:
            messagebox.showerror("Error", r.get("error", "Login failed"))
    except Exception as e:
        messagebox.showerror("Error", str(e))

tk.Button(root, text="Login", command=login).pack()
tk.Button(root, text="Register", command=register).pack()
root.mainloop()
