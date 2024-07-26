"""download an apple image"""
import requests
import os

# Define a more reliable URL for the apple PNG image
url = "https://external-content.duckduckgo.com/iu/?u=https%3A%2F%2Ftse1.mm.bing.net%2Fth%3Fid%3DOIP.q3hhyPUuKnHFQB-AtIaRgwHaFj%26pid%3DApi&f=1&ipt=a75b04a7a5c4c4757316865e35d0d18be0b108bbbffb45839fb9cc49a9282567&ipo=images"

# Send a GET request to the URL
response = requests.get(url)

# Path to save the image: Desktop/apple.png
desktop_path = os.path.join(os.path.expanduser("~"), "Desktop", "apple.png")

# Write the image data to a file
with open(desktop_path, "wb") as file:
    file.write(response.content)
    
print(f"Image has been downloaded to {desktop_path}")
