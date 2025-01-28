import google.generativeai as genai

genai.configure(api_key="enter your key here")
model = genai.GenerativeModel("gemini-1.5-flash")

product_name = "Smartphone with 5G connectivity"

response = model.generate_content(f"Generate a product description for {product_name}")
print(response.text)


