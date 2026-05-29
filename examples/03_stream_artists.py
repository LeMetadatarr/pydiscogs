"""Stream artists and show aliases / members / groups."""
import pydiscogs


def main() -> None:
    for artist in pydiscogs.stream("artists", limit=10):
        print(f"{artist.id}  {artist.name}")
        if artist.real_name:
            print(f"    real name: {artist.real_name}")
        if artist.aliases:
            print(f"    aliases: {', '.join(artist.aliases)}")
        if artist.members:
            print(f"    members: {', '.join(artist.members)}")


if __name__ == "__main__":
    main()
