allowed_extensions = [".txt", ".csv", ".dat"]

class InputLoader:
    def __init__(self, filename):
        pass

    def filenameExists(self, filename: str) -> bool:
        if os.path.exists(filename):
            return True
        else:
            return False
    
    def readNameDomains(self):
        with open(self.filename) as f:
            fileContent = f.readlines()
        self.nameDomains = [i.strip() for i in fileContent]
    
    def load(self):
        self.checkFileExtension()
        if self.filenameExists(filename):
            self.filename = filename
        else:
            raise FileNotFoundError(f"Provided filename `{filename}` does not exist. Please provide a valid filename.")

    def checkFileExtension(self, filename: str):
        ext = filename.split(".")[1]
        if file_type not in allowed_extensions:
            raise valueError(f"Unsupported extension `{ext}`. Expected of of: {', '.join(allowed_extensions)}")