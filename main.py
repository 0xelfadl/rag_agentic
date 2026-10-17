from pathlib import Path

def main():
    files= sorted(Path("data").glob("*.md"))
    print(f"Found {len(files)} documents:")
    for file in files:
        text= file.read_text(encoding="utf-8")
        print(f"- {file.name} : {len(text)} caracters")


if __name__ == "__main__":
    main()
