def get_key(key, file_name = "API.md"):
    with open(file_name, 'r') as file:
        for line in file:
            if line.startswith(key):
                return line.split('=')[1].strip()
    return None

def int_response(question):
    """
    This function returns the response of the API as an integer.
    """
    while True:
        rep = input(question)
        try:
            rep = int(rep)
            break  # Si ça marche, on sort de la boucle
        except ValueError:
            print("Ce n'est pas un entier valide. Réessayez.")