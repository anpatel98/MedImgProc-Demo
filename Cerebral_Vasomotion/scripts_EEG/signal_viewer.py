import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
import numpy as np


class SignalViewer:
    def __init__(self, signals, initial_bad_channels=None):
        self.signals = signals  # Input signals
        self.bad_channels = set(initial_bad_channels if initial_bad_channels.all() else [])  # Initial bad channels
        self.signals_per_page = 16  # Number of signals to display per page (8 rows, 2 columns)
        self.current_page = 0  # Current page

        self.window = tk.Tk()
        self.window.title("Signal Channel Viewer")
        self.window.geometry("1600x1200")  # Adjust the window size for a 2-column layout

        # Create a canvas with scrollbars
        self.main_frame = tk.Frame(self.window)
        self.main_frame.pack(fill=tk.BOTH, expand=1)

        self.canvas = tk.Canvas(self.main_frame)
        self.scrollbar_y = tk.Scrollbar(self.main_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.scrollbar_x = tk.Scrollbar(self.main_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        self.scrollable_frame = tk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar_y.set, xscrollcommand=self.scrollbar_x.set)

        # Add canvas and scrollbars to the window
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)

        # Add page navigation buttons
        self.button_frame = tk.Frame(self.window)
        self.button_frame.pack()

        self.prev_button = tk.Button(self.button_frame, text="Previous Page", command=self.prev_page)
        self.prev_button.pack(side=tk.LEFT, padx=10)

        self.next_button = tk.Button(self.button_frame, text="Next Page", command=self.next_page)
        self.next_button.pack(side=tk.LEFT, padx=10)

        # Show bad channel button
        self.bad_channel_button = tk.Button(self.button_frame, text="Show Bad Channels", command=self.show_bad_channels)
        self.bad_channel_button.pack(side=tk.LEFT, padx=10)

        # Result label
        self.result_label = tk.Label(self.window, text="")
        self.result_label.pack(pady=20)

        # Bind mouse scroll events to support scrolling
        self.bind_mouse_scroll()

        # Initialize and display signals
        self.display_signals()

    def bind_mouse_scroll(self):
        """Bind the mouse scroll to the canvas for vertical scrolling."""
        # Windows and MacOS
        self.canvas.bind_all("<MouseWheel>", self.on_mousewheel)
        # Linux (X11)
        self.canvas.bind_all("<Button-4>", self.on_mousewheel)
        self.canvas.bind_all("<Button-5>", self.on_mousewheel)

    def on_mousewheel(self, event):
        """Handle mouse scroll event for vertical scrolling."""
        if event.num == 4 or event.delta > 0:
            self.canvas.yview_scroll(-1, "units")  # Scroll up
        elif event.num == 5 or event.delta < 0:
            self.canvas.yview_scroll(1, "units")  # Scroll down

    def plot_signal_with_button(self, signal_index, parent_frame, row, col):
        # Create a sub-frame to hold the signal and button
        signal_frame = tk.Frame(parent_frame)
        signal_frame.grid(row=row, column=col, padx=10, pady=5)

        # Add signal index label
        index_label = tk.Label(signal_frame, text=f'Channel {signal_index}', font=("Arial", 10))
        index_label.pack(side=tk.LEFT, padx=5)

        # Get signal and compute its min/max
        signal = self.signals[signal_index]
        min_val = np.min(signal)
        max_val = np.max(signal)

        # Plot signal
        fig, ax = plt.subplots(figsize=(3, 1))
        ax.plot(signal)
        ax.set_ylim([min_val - 0.1 * abs(min_val), max_val + 0.1 * abs(max_val)])
        ax.axis('off')

        # Display max and min values
        max_min_label = tk.Label(signal_frame, text=f"Max: {max_val:.2f}\nMin: {min_val:.2f}", font=("Arial", 8))
        max_min_label.pack(side=tk.RIGHT, padx=5)

        # Embed matplotlib plot into Tkinter
        canvas_fig = FigureCanvasTkAgg(fig, master=signal_frame)
        canvas_fig.draw()
        canvas_fig.get_tk_widget().pack(side=tk.LEFT, padx=5)

        # Add button to toggle bad/good status
        def toggle_channel_status():
            if signal_index in self.bad_channels:
                self.bad_channels.remove(signal_index)
                button.config(text="Good", bg="blue")
            else:
                self.bad_channels.add(signal_index)
                button.config(text="Bad", bg="red")

        # Initial button state
        if signal_index in self.bad_channels:
            button = tk.Button(signal_frame, text="Bad", bg="red", command=toggle_channel_status)
        else:
            button = tk.Button(signal_frame, text="Good", bg="blue", command=toggle_channel_status)
        button.pack(side=tk.RIGHT, padx=5)

        # Close plot to save memory
        plt.close(fig)

    def display_signals(self):
        # Clear the current display
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        # Calculate the range of signals to display
        start_index = self.current_page * self.signals_per_page
        end_index = min(start_index + self.signals_per_page, len(self.signals))

        # Create an 8-row, 2-column layout
        row, col = 0, 0
        for i in range(start_index, end_index):
            self.plot_signal_with_button(i, self.scrollable_frame, row, col)
            col += 1
            if col > 1:  # If current column exceeds 1, move to the next row
                col = 0
                row += 1

    def next_page(self):
        if (self.current_page + 1) * self.signals_per_page < len(self.signals):
            self.current_page += 1
            self.display_signals()

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.display_signals()

    def show_bad_channels(self):
        self.result_label.config(text=f"Bad Channels: {sorted(self.bad_channels)}")
        print(f"Bad Channels: {sorted(self.bad_channels)}")

    def run(self):
        self.window.mainloop()

    def get_bad_channels(self):
        return sorted(self.bad_channels)

    def get_data(self):
        # Convert the set of bad channels to a list
        bad_channel_list = sorted(list(self.bad_channels))

        # Create a boolean mask for good channels
        good_channel_mask = np.ones(self.signals.shape[0], dtype=bool)
        good_channel_mask[bad_channel_list] = False

        # Filter signals and remaining channels
        filtered_sig_out = self.signals[good_channel_mask, :]
        remaining_channels = np.arange(self.signals.shape[0])[good_channel_mask]

        # Return the good signals and their count
        return filtered_sig_out, remaining_channels


# Example usage:
if __name__ == "__main__":
    signals = np.random.randn(32, 1000)  # Example signal data (32 channels, 1000 samples each)
    initial_bad_channels = [1, 5, 10]  # Predefined bad channels (can be input by the user)
    viewer = SignalViewer(signals, initial_bad_channels)
    viewer.run()

    # After the user interacts with the UI, you can get the filtered good signals and their count
    good_signals, good_signal_count = viewer.get_data()
    print(f"Good Signals: {good_signal_count}")
