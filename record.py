import pyautogui
import pynput
from pynput.mouse import Listener as MouseListener
import keyboard
import threading
import time

recording = False
replay = False
actions = []
save_file = "mouse_actions.txt"
replay_count = 1  # Default number of times to replay

def on_click(x, y, button, pressed):
    if recording:
        actions.append(('click', x, y, button, pressed, time.time()))
        print(f"Recorded click at ({x}, {y}) with button {button} and pressed {pressed}")

def on_scroll(x, y, dx, dy):
    if recording:
        actions.append(('scroll', x, y, dx, dy, time.time()))
        print(f"Recorded scroll at ({x}, {y}) with delta ({dx}, {dy})")

def toggle_recording():
    global recording
    recording = not recording
    if recording:
        print("Recording started...")
        actions.clear()
        actions.append(('start', time.time()))
    else:
        print("Recording stopped.")
        actions.append(('end', time.time()))
        save_actions()

def save_actions():
    with open(save_file, 'w') as f:
        for action in actions:
            f.write(','.join(map(str, action)) + '\n')
    print("Actions saved to", save_file)

def load_actions():
    global actions
    try:
        with open(save_file, 'r') as f:
            actions = [line.strip().split(',') for line in f]
            for i in range(len(actions)):
                if actions[i][0] == 'click':
                    actions[i] = (actions[i][0], int(actions[i][1]), int(actions[i][2]), actions[i][3], actions[i][4] == 'True', float(actions[i][5]))
                elif actions[i][0] == 'scroll':
                    actions[i] = (actions[i][0], int(actions[i][1]), int(actions[i][2]), int(actions[i][3]), int(actions[i][4]), float(actions[i][5]))
                elif actions[i][0] == 'start' or actions[i][0] == 'end':
                    actions[i] = (actions[i][0], float(actions[i][1]))
        print("Actions loaded from", save_file)
    except FileNotFoundError:
        print("No saved actions found.")

def record():
    with MouseListener(on_click=on_click, on_scroll=on_scroll) as mouse_listener:
        mouse_listener.join()

def replay_actions(count):
    global replay
    replay = True
    for _ in range(count):
        if not replay:
            break
        start_time = time.time()
        previous_timestamp = None
        for action in actions:
            if not replay:
                break
            action_type = action[0]
            if action_type == 'start':
                previous_timestamp = float(action[1])
                continue
            elif action_type == 'end':
                break
            elif previous_timestamp is not None:
                current_timestamp = float(action[-1])
                delay = current_timestamp - previous_timestamp
                time.sleep(delay)
                previous_timestamp = current_timestamp

            if action_type == 'click':
                _, x, y, button, pressed, _ = action
                if pressed:
                    print(f"Clicking at ({x}, {y}) with button {button}")
                    pyautogui.click(x, y, button='left' if button == 'Button.left' else 'right')
            elif action_type == 'scroll':
                _, x, y, dx, dy, _ = action
                print(f"Scrolling at ({x}, {y}) with delta ({dx}, {dy})")
                pyautogui.scroll(dy, x=x, y=y)
    
    print("Replay completed.")
    replay = False

if __name__ == "__main__":
    load_actions()  # Load previously saved actions if any

    # Start a separate thread to listen for F9 key press
    def listen_for_f9():
        while True:
            keyboard.wait('F9')
            toggle_recording()

    threading.Thread(target=listen_for_f9, daemon=True).start()

    record_thread = threading.Thread(target=record)
    record_thread.start()

    while True:
        command = input("Type 'replay' followed by a number to replay actions that many times, or 'exit' to quit: ").strip().lower()
        if command.startswith('replay'):
            try:
                count = int(command.split()[1])
                replay_thread = threading.Thread(target=replay_actions, args=(count,))
                replay_thread.start()
            except (IndexError, ValueError):
                print("Please specify the number of times to replay.")
        elif command == 'exit':
            replay = False
            break
