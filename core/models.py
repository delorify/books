
# Create your models here.
from django.conf import settings
from django.db import models


class Category(models.Model):
    """
    High-level book category/genre (e.g. Fiction, Sci-Fi).
    Designed to be simple for now, but can be extended later
    with hierarchy or localized titles.
    """

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Author(models.Model):
    name = models.CharField(max_length=200, unique=True)

    def __str__(self) -> str:
        return self.name


class Book(models.Model):
    title = models.CharField(max_length=250)
    description = models.TextField(blank=True)
    cover_url = models.URLField(blank=True)
    year = models.IntegerField(null=True, blank=True)

    authors = models.ManyToManyField(Author, related_name="books", blank=True)
    categories = models.ManyToManyField(
        Category,
        related_name="books",
        blank=True,
    )

    # External source info (e.g. Open Library)
    source = models.CharField(max_length=50, blank=True)
    source_id = models.CharField(max_length=120, blank=True)

    # Paid books support
    is_paid = models.BooleanField(default=False)
    price = models.DecimalField(max_digits=8, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "title"]
        indexes = [
            models.Index(fields=["title"]),
            models.Index(fields=["source", "source_id"]),
            models.Index(fields=["is_paid"]),
        ]

    def __str__(self) -> str:
        return self.title

    @property
    def is_free(self) -> bool:
        return not self.is_paid or self.price == 0


class UserLibrary(models.Model):
    class Status(models.TextChoices):
        WISHLIST = "wishlist", "Хочу прочитать"
        READING = "reading", "Читаю"
        FINISHED = "finished", "Прочитано"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.WISHLIST,
    )
    # 0..100 overall completion percentage
    progress_percent = models.PositiveIntegerField(default=0)
    added_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "book")
        ordering = ["-updated_at"]

    def __str__(self) -> str:
        return f"{self.user} - {self.book} ({self.status})"

    @property
    def is_finished(self) -> bool:
        return self.status == self.Status.FINISHED


class Purchase(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    currency = models.CharField(max_length=10, default="USD")
    provider = models.CharField(max_length=50, default="stripe")
    provider_payment_id = models.CharField(max_length=120, blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.COMPLETED,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "book")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Purchase: {self.user} -> {self.book}"


class BookChapter(models.Model):
    """
    Individual chapter/section of a book.
    Storing text per chapter keeps content manageable and
    allows us to paginate per chapter for the reader.
    """

    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="chapters")
    order = models.PositiveIntegerField()
    title = models.CharField(max_length=250, blank=True)
    content = models.TextField()

    class Meta:
        ordering = ["book", "order"]
        unique_together = ("book", "order")
        indexes = [
            models.Index(fields=["book", "order"]),
        ]

    def __str__(self) -> str:
        label = self.title or f"Chapter {self.order}"
        return f"{self.book.title} – {label}"


class BookPage(models.Model):
    """
    Stable, pre-generated page of a book.
    Pages are numbered globally within a book (1..N) but also
    keep their chapter and page index inside the chapter.
    """

    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="pages")
    chapter = models.ForeignKey(
        BookChapter, on_delete=models.CASCADE, related_name="pages"
    )
    number = models.PositiveIntegerField()
    chapter_page_index = models.PositiveIntegerField()
    content = models.TextField()

    class Meta:
        ordering = ["book", "number"]
        unique_together = ("book", "number")
        indexes = [
            models.Index(fields=["book", "number"]),
            models.Index(fields=["chapter", "chapter_page_index"]),
        ]

    def __str__(self) -> str:
        return f"{self.book.title} – page {self.number}"


class ReadingProgress(models.Model):
    """
    Per-user detailed reading location.
    Keeps track of chapter and a simple page index within that chapter.
    """

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    chapter = models.ForeignKey(BookChapter, on_delete=models.CASCADE)
    page_index = models.PositiveIntegerField(default=1)  # 1-based within chapter
    page = models.ForeignKey(
        BookPage,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reading_progress",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "book")
        ordering = ["-updated_at"]

    def __str__(self) -> str:
        return f"{self.user} @ {self.book} ch{self.chapter.order} p{self.page_index}"