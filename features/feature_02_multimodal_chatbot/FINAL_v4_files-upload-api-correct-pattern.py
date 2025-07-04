# CORRECT pattern -- upload first, then reference the returned file object
myfile = client.files.upload(file="path/to/file.png")
response = client.models.generate_content(
    model="gemini-2.5-pro",
    contents=[myfile, "\n\n", "Is file ke mutaliq kuch batao."]
)
