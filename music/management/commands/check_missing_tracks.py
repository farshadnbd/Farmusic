import json
import re
import time
import unicodedata
from urllib.parse import quote
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from django.core.management.base import BaseCommand

from music.models import Album


MUSICBRAINZ_BASE = "https://musicbrainz.org/ws/2"


class Command(BaseCommand):
    help = "Check FarMusic albums against MusicBrainz tracklists"

    def add_arguments(self, parser):
        parser.add_argument(
            "--album",
            type=int,
            help="Check only one album by ID",
        )

        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Show albums that are complete too",
        )

    def handle(self, *args, **options):

        album_id = options.get("album")
        verbose = options.get("verbose")

        if album_id:
            albums = Album.objects.filter(id=album_id).select_related("artist")
        else:
            albums = Album.objects.all().select_related("artist")

        total = albums.count()

        if total == 0:
            self.stdout.write(self.style.WARNING("No albums found."))
            return

        self.stdout.write(
            self.style.SUCCESS(
                f"Checking {total} album(s)..."
            )
        )

        for index, album in enumerate(albums, start=1):

            artist_name = album.artist.name if album.artist else ""
            album_title = album.title or ""

            self.stdout.write(
                f"\n[{index}/{total}] {artist_name} - {album_title}"
            )

            try:
                reference_tracks = self.find_musicbrainz_tracks(
                    artist_name,
                    album_title,
                )

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"  ERROR: {e}"
                    )
                )
                continue

            if reference_tracks is None:
                self.stdout.write(
                    self.style.WARNING(
                        "  MusicBrainz release not found."
                    )
                )
                continue

            site_tracks = list(
                album.music_set.values_list("title", flat=True)
            )

            missing = self.find_missing_tracks(
                reference_tracks,
                site_tracks,
            )

            if missing:

                self.stdout.write(
                    self.style.ERROR(
                        f"  MISSING: {len(missing)} track(s)"
                    )
                )

                for track in missing:
                    self.stdout.write(
                        f"    - {track}"
                    )

            elif verbose:

                self.stdout.write(
                    self.style.SUCCESS(
                        f"  OK: {len(site_tracks)} / "
                        f"{len(reference_tracks)} tracks"
                    )
                )

            else:

                self.stdout.write(
                    self.style.SUCCESS("  OK")
                )

    # ---------------------------------------------------------
    # MusicBrainz
    # ---------------------------------------------------------

    def musicbrainz_request(self, endpoint, params):

        query_string = "&".join(
            f"{quote(str(k))}={quote(str(v))}"
            for k, v in params.items()
        )

        url = f"{MUSICBRAINZ_BASE}/{endpoint}?{query_string}"

        request = Request(
            url,
            headers={
                "User-Agent": (
                    "FarMusicTrackChecker/1.0 "
                    "(https://farmusic.ir)"
                ),
                "Accept": "application/json",
            },
        )

        try:

            with urlopen(request, timeout=20) as response:

                data = response.read().decode("utf-8")

                return json.loads(data)

        except HTTPError as e:

            if e.code == 503:
                raise RuntimeError(
                    "MusicBrainz rate limit / temporary unavailable"
                )

            raise

        except URLError as e:

            raise RuntimeError(
                f"MusicBrainz connection error: {e}"
            )

    def find_musicbrainz_tracks(self, artist_name, album_title):

        if not artist_name or not album_title:
            return None

        # Search for the album/release.
        query = (
            f'release:"{album_title}" '
            f'AND artist:"{artist_name}"'
        )

        data = self.musicbrainz_request(
            "release",
            {
                "query": query,
                "fmt": "json",
                "limit": 10,
            },
        )

        releases = data.get("releases", [])

        if not releases:
            return None

        # Prefer official releases.
        official = [
            release
            for release in releases
            if release.get("status") == "Official"
        ]

        if official:
            releases = official

        # MusicBrainz search score.
        releases.sort(
            key=lambda release: release.get("score", 0),
            reverse=True,
        )

        selected = releases[0]

        release_id = selected.get("id")

        if not release_id:
            return None

        # Respect MusicBrainz rate limiting.
        time.sleep(1.1)

        release_data = self.musicbrainz_request(
            f"release/{release_id}",
            {
                "inc": "recordings+media+artist-credits",
                "fmt": "json",
            },
        )

        tracks = []

        for medium in release_data.get("media", []):

            for track in medium.get("tracks", []):

                title = track.get("title")

                if title:
                    tracks.append(title)

        return tracks

    # ---------------------------------------------------------
    # Normalization
    # ---------------------------------------------------------

    def normalize_title(self, title):

        if not title:
            return ""

        title = unicodedata.normalize(
            "NFKC",
            str(title),
        )

        # Arabic/Persian normalization
        replacements = {
            "ي": "ی",
            "ى": "ی",
            "ك": "ک",
            "ۀ": "ه",
            "ة": "ه",
            "أ": "ا",
            "إ": "ا",
            "ؤ": "و",
        }

        for old, new in replacements.items():
            title = title.replace(old, new)

        title = title.lower()

        # Remove common feature notation.
        title = re.sub(
            r"\b(feat\.?|ft\.?|featuring)\b",
            "",
            title,
            flags=re.IGNORECASE,
        )

        # Remove punctuation.
        title = re.sub(
            r"[^\w\sآ-ی]",
            " ",
            title,
            flags=re.UNICODE,
        )

        # Collapse whitespace.
        title = re.sub(
            r"\s+",
            " ",
            title,
        )

        return title.strip()

    # ---------------------------------------------------------
    # Compare
    # ---------------------------------------------------------

    def find_missing_tracks(
        self,
        reference_tracks,
        site_tracks,
    ):

        normalized_site = {
            self.normalize_title(track)
            for track in site_tracks
            if track
        }

        missing = []

        for reference_track in reference_tracks:

            normalized_reference = self.normalize_title(
                reference_track
            )

            if not normalized_reference:
                continue

            if normalized_reference not in normalized_site:

                missing.append(reference_track)

        return missing