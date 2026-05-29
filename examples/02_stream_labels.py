"""Stream the first labels from the live dump (no full download)."""
import pydiscogs


def main() -> None:
    for label in pydiscogs.stream("labels", limit=10):
        print(label.id, "-", label.name)


if __name__ == "__main__":
    main()
