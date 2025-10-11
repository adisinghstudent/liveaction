import google.generativeai as genai
import mss
import os
from PIL import Image
import sys

# IMPORTANT: Replace with your actual Gemini API key
GEMINI_API_KEY = "AIzaSyB4yPcHciQ1qmiUBPnihDh3UQFMqNpTX70"

try:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')
except Exception as e:
    print(f"Error configuring Gemini API: {e}")
    print("Please make sure you have set your GEMINI_API_KEY correctly.")
    sys.exit()

def take_screenshot():
    """Takes a screenshot and saves it as screenshot.png."""
    with mss.mss() as sct:
        filename = sct.shot(output="screenshot.png")
        print(f"Screenshot saved as {filename}")
        return filename

def describe_screenshot(question):
    """Describes the screenshot using the Gemini API based on a user's question."""
    print("Analyzing screenshot...")
    try:
        img = Image.open("screenshot.png")
        response = model.generate_content([question, img])
        print("\n--- Gemini's Answer ---")
        print(response.text)
        print("-----------------------\n")
    except Exception as e:
        print(f"Error generating content: {e}")
    finally:
        # Clean up the screenshot file
        if os.path.exists("screenshot.png"):
            os.remove("screenshot.png")

def main():
    """Main function to run the application."""
    print("Ask a question about the screen, or type 'exit' to quit.")
    while True:
        question = input("> ")
        if question.lower() in ['exit', 'quit']:
            break
        take_screenshot()
        describe_screenshot(question)


if __name__ == "__main__":
    main()