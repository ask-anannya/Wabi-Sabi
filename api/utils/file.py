import os

# Every caller passes paths like "prompts/xyz.prompt" relative to the api/
# package root — that only happened to work because Docker's WORKDIR is set
# to api/, making it equal to the process's CWD. Serverless runtimes (e.g.
# Vercel) don't guarantee that, so relative paths are anchored here instead,
# against api/ itself (one level up from utils/), independent of CWD.
_API_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def return_file_contents(file_path) -> str:
    if not os.path.isabs(file_path):
        file_path = os.path.join(_API_ROOT, file_path)

    contents = ""
    try:
        with open(file_path, 'r', encoding="utf-8") as file:
            contents = file.read()
    except UnicodeDecodeError:
        print("UTF-8 decoding failed, trying latin1.")
        with open(file_path, encoding="latin1") as f:
            contents = f.read()
    finally:
        if contents == "":
            raise Exception("File is empty or could not be read.")
    return contents
