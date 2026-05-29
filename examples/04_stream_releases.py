"""Stream releases and print credits, formats and tracklist."""
import pydiscogs


def main() -> None:
    for release in pydiscogs.stream("releases", limit=3):
        artists = ", ".join(a.name for a in release.artists)
        print(f"[{release.id}] {artists} - {release.title} ({release.year})")
        print(f"    country: {release.country}  labels: {', '.join(release.labels)}")
        print(f"    genres: {', '.join(release.genres)}  styles: {', '.join(release.styles)}")
        for fmt in release.formats:
            print(f"    format: {fmt.name} x{fmt.qty} {fmt.descriptions}")
        for track in release.tracklist:
            print(f"      {track.position:<4} {track.title} ({track.duration})")
        print()


if __name__ == "__main__":
    main()
