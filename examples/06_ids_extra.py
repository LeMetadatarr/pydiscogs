"""Build the canonical metadatarr ExternalIds.extra dict from a release."""
import pydiscogs


def main() -> None:
    release = next(pydiscogs.stream("releases", limit=1))
    extra = pydiscogs.release_to_extra(release)
    for key, value in extra.items():
        print(f"{key} = {value}")

    # the same dispatch works for any entity
    label = next(pydiscogs.stream("labels", limit=1))
    print(pydiscogs.to_extra(label))


if __name__ == "__main__":
    main()
