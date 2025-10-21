import json
from rhinomcp.tools.get_document_info import get_document_info
from rhinomcp.tools.create_text import create_text
from rhinomcp.tools.create_text_dot import create_text_dot
from rhinomcp.tools.create_leader import create_leader


def main():
    print("-- get_document_info --")
    print(get_document_info(None))

    print("\n-- create_text tool --")
    print(create_text(None, "Hello Rhino", [0, 0, 0], 1.5, "Text-One", [255, 0, 0]))

    print("\n-- create_text_dot tool --")
    print(create_text_dot(None, "P1", [1, 1, 0], "Dot-One", [0, 0, 255]))

    print("\n-- create_leader tool --")
    print(
        create_leader(None, points=[[0, 0, 0], [5, 0, 0]], text="Edge A", name="Leader A")
    )


if __name__ == "__main__":
    main()


