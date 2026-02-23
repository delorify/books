from __future__ import annotations

from django.core.management.base import BaseCommand

from core.models import Author, Book, BookChapter


DEMO_BOOKS = [
    {
        "title": "Pride and Prejudice",
        "author": "Jane Austen",
        "year": 1813,
        "description": "A classic comedy of manners about the Bennet sisters, love, and social expectations.",
        "cover_url": "https://covers.openlibrary.org/b/id/8081536-L.jpg",
        "source_id": "demo-pride-prejudice",
        "chapters": [
            {
                "title": "Chapter 1",
                "content": (
                    "It is a truth universally acknowledged, that a single man in possession of a good fortune, "
                    "must be in want of a wife.\n\n"
                    "However little known the feelings or views of such a man may be on his first entering a neighbourhood, "
                    "this truth is so well fixed in the minds of the surrounding families, that he is considered the rightful "
                    "property of someone or other of their daughters."
                ),
            },
            {
                "title": "Chapter 2",
                "content": (
                    "Mr. Bennet was among the earliest of those who waited on Mr. Bingley. "
                    "He had always intended to visit him, though to the last always assuring his wife that he should not go."
                ),
            },
        ],
    },
    {
        "title": "The Adventures of Sherlock Holmes",
        "author": "Arthur Conan Doyle",
        "year": 1892,
        "description": "Short stories featuring the legendary detective Sherlock Holmes and Dr. Watson.",
        "cover_url": "https://covers.openlibrary.org/b/id/8228691-L.jpg",
        "source_id": "demo-sherlock-holmes",
        "chapters": [
            {
                "title": "A Scandal in Bohemia",
                "content": (
                    "To Sherlock Holmes she is always the woman. I have seldom heard him mention her under any other name. "
                    "In his eyes she eclipses and predominates the whole of her sex."
                ),
            }
        ],
    },
    {
        "title": "Moby-Dick",
        "author": "Herman Melville",
        "year": 1851,
        "description": "The epic tale of Captain Ahab’s obsessive quest to hunt the white whale.",
        "cover_url": "https://covers.openlibrary.org/b/id/7222246-L.jpg",
        "source_id": "demo-moby-dick",
        "chapters": [
            {
                "title": "Loomings",
                "content": (
                    "Call me Ishmael. Some years ago—never mind how long precisely—having little or no money in my purse, "
                    "and nothing particular to interest me on shore, I thought I would sail about a little and see the watery part of the world."
                ),
            }
        ],
    },
    {
        "title": "Crime and Punishment",
        "author": "Fyodor Dostoyevsky",
        "year": 1866,
        "description": "A psychological novel exploring guilt, morality, and redemption in St Petersburg.",
        "cover_url": "https://covers.openlibrary.org/b/id/8231856-L.jpg",
        "source_id": "demo-crime-punishment",
        "chapters": [
            {
                "title": "Part I, Chapter 1",
                "content": (
                    "On an exceptionally hot evening early in July a young man came out of the garret in which he lodged in S. Place "
                    "and walked slowly, as though in hesitation, towards K. bridge."
                ),
            }
        ],
    },
    {
        "title": "Anna Karenina",
        "author": "Leo Tolstoy",
        "year": 1878,
        "description": "A sweeping Russian novel about love, family, and society.",
        "cover_url": "https://covers.openlibrary.org/b/id/8101351-L.jpg",
        "source_id": "demo-anna-karenina",
        "chapters": [
            {
                "title": "Part I, Chapter 1",
                "content": (
                    "All happy families are alike; each unhappy family is unhappy in its own way."
                ),
            }
        ],
    },
    {
        "title": "Great Expectations",
        "author": "Charles Dickens",
        "year": 1861,
        "description": "The coming-of-age story of Pip, an orphan with great expectations.",
        "cover_url": "https://covers.openlibrary.org/b/id/8225631-L.jpg",
        "source_id": "demo-great-expectations",
        "chapters": [
            {
                "title": "Chapter 1",
                "content": (
                    "My father's family name being Pirrip, and my Christian name Philip, my infant tongue could make of both names nothing "
                    "longer or more explicit than Pip. So, I called myself Pip, and came to be called Pip."
                ),
            }
        ],
    },
    {
        "title": "The Picture of Dorian Gray",
        "author": "Oscar Wilde",
        "year": 1890,
        "description": "A philosophical novel about beauty, youth, and moral corruption.",
        "cover_url": "https://covers.openlibrary.org/b/id/8091016-L.jpg",
        "source_id": "demo-dorian-gray",
        "chapters": [
            {
                "title": "Chapter 1",
                "content": (
                    "The studio was filled with the rich odour of roses, and when the light summer wind stirred amidst the trees of the garden, "
                    "there came through the open door the heavy scent of the lilac, or the more delicate perfume of the pink-flowering thorn."
                ),
            }
        ],
    },
    {
        "title": "Kөkserek",
        "author": "Мұхтар Әуезов",
        "year": 1929,
        "description": "Классикалық қазақ повесі қасқыр мен адам тағдыры туралы.",
        "cover_url": "https://covers.openlibrary.org/b/id/10523354-L.jpg",
        "source_id": "demo-kokserek",
        "chapters": [
            {
                "title": "Басы",
                "content": (
                    "Қыстың ақ бораны уілдеп тұр. Түн. Қара бұлт қаптаған аспан астында айсыз боран ауылды басып қалған."
                ),
            }
        ],
    },
    {
        "title": "Fathers and Sons",
        "author": "Ivan Turgenev",
        "year": 1862,
        "description": "A novel about generational conflict and nihilism in 19th‑century Russia.",
        "cover_url": "https://covers.openlibrary.org/b/id/8231852-L.jpg",
        "source_id": "demo-fathers-sons",
        "chapters": [
            {
                "title": "Chapter 1",
                "content": (
                    "‘Well, Piotr, still not in sight?’ was the question asked on May the 20th, 1859, by a gentleman of a little over forty, "
                    "wearing a dusty cloak and checked trousers, who came out without his hat on to the low steps of the posting-station "
                    "at X."
                ),
            }
        ],
    },
    {
        "title": "The Brothers Karamazov",
        "author": "Fyodor Dostoyevsky",
        "year": 1880,
        "description": "A profound exploration of faith, doubt, and free will through the story of three brothers.",
        "cover_url": "https://covers.openlibrary.org/b/id/8235114-L.jpg",
        "source_id": "demo-brothers-karamazov",
        "chapters": [
            {
                "title": "Book I, Chapter 1",
                "content": (
                    "Alexey Fyodorovich Karamazov was the third son of Fyodor Pavlovich Karamazov, a landowner well known in our district "
                    "in his own day, and still remembered among us owing to his gloomy and tragic death."
                ),
            }
        ],
    },
]


class Command(BaseCommand):
  help = "Load demo public-domain books with chapter content into the database."

  def handle(self, *args, **options):
    created_count = 0
    for data in DEMO_BOOKS:
      author, _ = Author.objects.get_or_create(name=data["author"])

      book, created = Book.objects.get_or_create(
        title=data["title"],
        source="demo",
        source_id=data["source_id"],
        defaults={
          "description": data["description"],
          "cover_url": data["cover_url"],
          "year": data["year"],
          "is_paid": False,
          "price": 0,
        },
      )
      book.authors.add(author)

      if created:
        self.stdout.write(self.style.SUCCESS(f"Created demo book: {book.title}"))
      else:
        self.stdout.write(f"Updated/kept demo book: {book.title}")

      # (Re)create chapters
      book.chapters.all().delete()
      for idx, chapter_data in enumerate(data["chapters"], start=1):
        BookChapter.objects.create(
          book=book,
          order=idx,
          title=chapter_data["title"],
          content=chapter_data["content"],
        )

      created_count += 1

    self.stdout.write(self.style.SUCCESS(f"Demo books loaded: {created_count}"))

