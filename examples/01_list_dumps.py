"""List the dump objects available for the latest year."""
import pydiscogs


def main() -> None:
    for dump in pydiscogs.list_dumps():
        print(f"{dump.date}  {dump.entity:<9}  {dump.filename}")


if __name__ == "__main__":
    main()
