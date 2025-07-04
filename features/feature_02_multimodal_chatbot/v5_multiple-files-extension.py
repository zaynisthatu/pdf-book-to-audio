# Extended to N files: upload each individually, pass all as a list + prompt
uploaded_files = [client.files.upload(file=p) for p in file_paths if os.path.isfile(p)]
response = client.models.generate_content(
    model="gemini-2.5-pro",
    contents=uploaded_files + ["\n\n", "In tamam files ke mutaliq kuch batao."]
)
