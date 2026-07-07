from django.core.management.base import BaseCommand

from apps.pois.tasks import reindex_all_pois


class Command(BaseCommand):
    help = "Rebuild the Meilisearch POI index from the database (runs inline, not via worker)"

    def handle(self, *args, **options):
        from services import search

        if not search.enabled():
            self.stdout.write(self.style.WARNING("Meilisearch disabled (MEILI_URL not set)"))
            return
        count = reindex_all_pois()
        self.stdout.write(self.style.SUCCESS(f"Indexed {count} POIs"))
