"""
IP Camera Monitor
Author: Gamm3r96
Copyright © 2024 Gamm3r96. All rights reserved.
"""

import cv2
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox, Toplevel
from PIL import Image, ImageTk
from urllib.parse import quote
import os

class IPMonitorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("IP Camera Monitor")
        self.root.geometry("500x450")
        self.style = ttk.Style("flatly")

        self.video_source = None
        self.is_floating = False
        self.floating_window = None
        self.is_recording = False
        self.out = None
        self.video_directory = "recorded_videos"

        # Ensure the directory exists
        if not os.path.exists(self.video_directory):
            os.makedirs(self.video_directory)

        # IP and Port Inputs
        self.ip_label = ttk.Label(root, text="IP Address:", bootstyle="primary")
        self.ip_label.pack(pady=5)
        self.ip_entry = ttk.Entry(root, bootstyle="primary")
        self.ip_entry.pack(pady=5)

        self.port_label = ttk.Label(root, text="Port:", bootstyle="primary")
        self.port_label.pack(pady=5)
        self.port_entry = ttk.Entry(root, bootstyle="primary")
        self.port_entry.pack(pady=5)

        # Username and Password Inputs
        self.username_label = ttk.Label(root, text="Username:", bootstyle="primary")
        self.username_label.pack(pady=5)
        self.username_entry = ttk.Entry(root, bootstyle="primary")
        self.username_entry.pack(pady=5)

        self.password_label = ttk.Label(root, text="Password:", bootstyle="primary")
        self.password_label.pack(pady=5)
        self.password_entry = ttk.Entry(root, show="*", bootstyle="primary")
        self.password_entry.pack(pady=5)

        # Streaming URL Input
        self.url_label = ttk.Label(root, text="Streaming URL:", bootstyle="primary")
        self.url_label.pack(pady=5)
        self.url_entry = ttk.Entry(root, width=50, bootstyle="primary")
        self.url_entry.pack(pady=5)

        self.connect_button = ttk.Button(root, text="Connect", command=self.connect_to_camera, bootstyle="success")
        self.connect_button.pack(pady=10)

        self.floating_button = ttk.Button(root, text="Toggle Floating Video", command=self.toggle_floating_video, bootstyle="info")
        self.floating_button.pack(pady=10)

        self.record_button = ttk.Button(root, text="Start Recording", command=self.toggle_recording, bootstyle="warning")
        self.record_button.pack(pady=10)

        self.canvas = ttk.Canvas(root, width=640, height=480, bootstyle="dark")
        self.canvas.pack()
        self.canvas.pack_forget()  # Initially hide the canvas

        # Button animations
        self.connect_button.bind("<Enter>", self.on_button_hover)
        self.connect_button.bind("<Leave>", self.on_button_leave)

        self.floating_button.bind("<Enter>", self.on_button_hover)
        self.floating_button.bind("<Leave>", self.on_button_leave)

        self.record_button.bind("<Enter>", self.on_button_hover)
        self.record_button.bind("<Leave>", self.on_button_leave)

    def connect_to_camera(self):
        url = self.url_entry.get()
        ip = self.ip_entry.get()
        port = self.port_entry.get()
        username = self.username_entry.get()
        password = self.password_entry.get()

        if url:
            if username and password:
                # Prepend username and password for basic authentication
                url = self.add_auth_to_url(url, username, password)
            self.start_video_stream(url)
        elif ip and port:
            if username and password:
                # Form URL with authentication for protected cameras
                camera_url = f"http://{quote(username)}:{quote(password)}@{ip}:{port}/video"
            else:
                camera_url = f"http://{ip}:{port}/video"
            self.start_video_stream(camera_url)
        else:
            messagebox.showerror("Input Error", "Please enter either a streaming URL or both IP address and port.")

    def add_auth_to_url(self, url, username, password):
        # Add username and password to URL for HTTP authentication
        parsed_url = url.split("://")
        return f"{parsed_url[0]}://{quote(username)}:{quote(password)}@{parsed_url[1]}"

    def start_video_stream(self, url):
        if self.video_source:
            self.video_source.release()

        self.video_source = cv2.VideoCapture(url)

        # Show the video in either the main window or the floating window
        if self.is_floating:
            self.canvas.pack_forget()
            if self.floating_window:
                self.floating_window.deiconify()
        else:
            self.canvas.pack()

        self.update_video()

    def update_video(self):
        if self.video_source is not None and self.video_source.isOpened():
            ret, frame = self.video_source.read()
            if ret:
                # Convert the frame to RGB
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                # Convert to Image
                img = Image.fromarray(frame)
                imgtk = ImageTk.PhotoImage(image=img)

                if self.is_floating and self.floating_window:
                    self.floating_window_canvas.create_image(0, 0, anchor=tk.NW, image=imgtk)
                    self.floating_window_canvas.image = imgtk
                else:
                    self.canvas.create_image(0, 0, anchor=tk.NW, image=imgtk)
                    self.canvas.image = imgtk

                if self.is_recording and self.out is not None:
                    self.out.write(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))  # Write frame to file

                self.root.after(10, self.update_video)
            else:
                messagebox.showerror("Stream Error", "Failed to grab frame.")
        else:
            messagebox.showerror("Connection Error", "Failed to connect to camera.")

    def toggle_floating_video(self):
        if self.is_floating:
            self.is_floating = False
            if self.floating_window:
                self.floating_window.withdraw()
            self.canvas.pack()
        else:
            self.is_floating = True
            self.create_floating_window()

    def create_floating_window(self):
        if not self.floating_window:
            self.floating_window = Toplevel(self.root)
            self.floating_window.title("Floating Video")
            self.floating_window_canvas = ttk.Canvas(self.floating_window, width=640, height=480, bootstyle="dark")
            self.floating_window_canvas.pack()
            self.floating_window.protocol("WM_DELETE_WINDOW", self.toggle_floating_video)
        else:
            self.floating_window.deiconify()

    def toggle_recording(self):
        if self.is_recording:
            self.stop_recording()
        else:
            self.start_recording()

    def start_recording(self):
        if not self.video_source or not self.video_source.isOpened():
            messagebox.showerror("Recording Error", "No video source connected.")
            return

        self.is_recording = True
        self.record_button.config(text="Stop Recording", bootstyle="danger")

        # Define video codec and create VideoWriter object
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        filename = os.path.join(self.video_directory, "video.avi")
        self.out = cv2.VideoWriter(filename, fourcc, 20.0, (640, 480))

    def stop_recording(self):
        if self.is_recording:
            self.is_recording = False
            self.record_button.config(text="Start Recording", bootstyle="warning")
            if self.out is not None:
                self.out.release()

    def on_button_hover(self, event):
        event.widget.config(bootstyle="success-outline")

    def on_button_leave(self, event):
        event.widget.config(bootstyle="success")

    def __del__(self):
        if self.video_source:
            self.video_source.release()
        if self.out:
            self.out.release()

if __name__ == "__main__":
    root = ttk.Window(themename="darkly")
    app = IPMonitorApp(root)
    root.mainloop()
