def get_key(key, file_name = "API.md"):
    with open(file_name, 'r') as file:
        for line in file:
            if line.startswith(key):
                return line.split('=')[1].strip()
    return None