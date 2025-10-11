
import google.generativeai as genai
import mss
import os
from pynput import keyboard
from PIL import Image

# IMPORTANT: Replace with your actual Gemini API key
GEMINI_API_KEY = "AIzaSyB4yPcHciQ1qmiUBPnihDh3UQFMqNpTX70"

try:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')
except Exception as e:
    print(f"Error configuring Gemini API: {e}")
    print("Please make sure you have set your GEMINI_API_KEY correctly.")
    exit()

def take_screenshot():
    """Takes a screenshot and saves it as screenshot.png."""
    with mss.mss() as sct:
        filename = sct.shot(output="screenshot.png")
        print(f"Screenshot saved as {filename}")
        return filename

def describe_screenshot():
    """Describes the screenshot using the Gemini API."""
    print("Analyzing screenshot...")
    try:
        img = Image.open("screenshot.png")
        response = model.generate_content(["What is in this image?", img])
        print("\n--- Image Description ---")
        print(response.text)
        print("-------------------------\n")
    except Exception as e:
        print(f"Error generating content: {e}")
    finally:
        # Clean up the screenshot file
        if os.path.exists("screenshot.png"):
            os.remove("screenshot.png")

def on_press(key):
    """Handles key press events."""
    if key == keyboard.Key.enter:
        print("Enter key pressed, taking screenshot...")
        take_screenshot()
        describe_screenshot()

def on_release(key):
    """Handles key release events."""
    if key == keyboard.Key.esc:
        # Stop listener
        return False

def main():
    """Main function to run the application."""
    print("Press Enter to take a screenshot and get a description.")
    print("Press Esc to exit.")

    # Collect events until released
    with keyboard.Listener(
            on_press=on_press,
            on_release=on_release) as listener:
        listener.join()

if __name__ == "__main__":
    main()
