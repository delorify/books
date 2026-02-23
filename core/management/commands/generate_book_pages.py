from __future__ import annotations

from django.core.management.base import BaseCommand

from core.models import Book, BookChapter, BookPage


PAGE_CHAR_LIMIT = 1500


def generate_pages_for_book(book: Book, *, stdout=None) -> int:
    """
    Generate BookPage rows for a given book from its chapters.
    Stable pagination based on fixed character window. If chapter
    content doesn't change, page numbers stay the same.
    """
    chapters = list(BookChapter.objects.filter(book=book).order_by("order"))
    if not chapters:
        if stdout:
            stdout.write(f"No chapters for book: {book.title}")
        return 0

    BookPage.objects.filter(book=book).delete()

    page_number = 1
    for chapter in chapters:
        text = chapter.content or ""
        chapter_page_index = 1
        start = 0
        length = len(text)
        while start < length:
            end = min(start + PAGE_CHAR_LIMIT, length)
            chunk = text[start:end]
            BookPage.objects.create(
                book=book,
                chapter=chapter,
                number=page_number,
                chapter_page_index=chapter_page_index,
                content=chunk,
            )
            page_number += 1
            chapter_page_index += 1
            start = end

    if stdout:
        stdout.write(f"Generated {page_number - 1} pages for {book.title}")
    return page_number - 1


class Command(BaseCommand):
    help = "Generate stable BookPage entries for books based on their chapters."

    def add_arguments(self, parser):
        parser.add_argument(
            "--demo-only",
            action="store_true",
            help="Only generate pages for demo books (source='demo').",
        )

    def handle(self, *args, **options):
        demo_only: bool = options["demo_only"]
        qs = Book.objects.all()
        if demo_only:
            qs = qs.filter(source="demo")

        total_books = qs.count()
        self.stdout.write(f"Generating pages for {total_books} book(s)...")

        total_pages = 0
        for book in qs:
            total_pages += generate_pages_for_book(book, stdout=self.stdout)

        self.stdout.write(self.style.SUCCESS(f"Done. Total pages: {total_pages}"))

