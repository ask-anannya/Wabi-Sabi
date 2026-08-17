def return_file_contents(file_path)->str:
    contents = ""
    try:
        with open(file_path, 'r',encoding="utf-8") as file:
         contents = file.read()
    except UnicodeDecodeError:
        print("UTF-8 decoding failed, trying latin1.")
        with open("your_file.txt", encoding="latin1") as f:
            contents = f.read()
    finally:
        if contents == "":
            raise Exception("File is empty or could not be read.")
    return contents