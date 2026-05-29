"""Stream masters (recordings grouping their variant releases)."""
import pydiscogs


def main() -> None:
    for master in pydiscogs.stream("masters", limit=10):
        artists = ", ".join(a.name for a in master.artists)
        print(f"{master.id}  {artists} - {master.title} ({master.year})")
        print(f"    main release: {master.main_release}  styles: {', '.join(master.styles)}")


if __name__ == "__main__":
    main()
