from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from core.management.commands.generate_book_pages import generate_pages_for_book

from .models import (
    Author,
    Book,
    BookChapter,
    BookPage,
    ReadingProgress,
    Purchase,
    UserLibrary,
)
from .services.openlibrary import search_books


def _get_continue_reading(user):
    if not user.is_authenticated:
        return None
    return (
        ReadingProgress.objects.select_related("book", "chapter", "page")
        .filter(user=user)
        .order_by("-updated_at")
        .first()
    )


def book_list(request):
    q = (request.GET.get("q") or "").strip()
    books = Book.objects.all()
    if q:
        books = books.filter(title__icontains=q)

    continue_item = _get_continue_reading(request.user)

    return render(
        request,
        "core/book_list.html",
        {
            "books": books,
            "q": q,
            "continue_item": continue_item,
        },
    )


def book_detail(request, pk: int):
    book = get_object_or_404(Book, pk=pk)
    in_library = False
    progress = None
    if request.user.is_authenticated:
        in_library = UserLibrary.objects.filter(user=request.user, book=book).exists()
        progress = (
            ReadingProgress.objects.select_related("chapter")
            .filter(user=request.user, book=book)
            .first()
        )
    return render(
        request,
        "core/book_detail.html",
        {
            "book": book,
            "in_library": in_library,
            "reading_progress": progress,
        },
    )


def import_search(request):
    query = (request.GET.get("query") or "").strip()
    results = search_books(query) if query else []
    return render(request, "core/import_search.html", {"query": query, "results": results})


@require_POST
@transaction.atomic
def import_add(request):
    title = (request.POST.get("title") or "").strip()
    source = (request.POST.get("source") or "").strip()
    source_id = (request.POST.get("source_id") or "").strip()
    cover_url = (request.POST.get("cover_url") or "").strip()
    year_raw = (request.POST.get("year") or "").strip()
    authors_raw = (request.POST.get("authors") or "").strip()

    if not title:
        messages.error(request, "Не удалось добавить книгу: пустое название.")
        return redirect("import_search")

    year = None
    if year_raw.isdigit():
        year = int(year_raw)

    # Не создаём дубликаты по source+source_id (если source_id есть)
    book = None
    if source and source_id:
        book = Book.objects.filter(source=source, source_id=source_id).first()

    if book is None:
        book = Book.objects.create(
            title=title,
            year=year,
            cover_url=cover_url,
            source=source,
            source_id=source_id,
        )

        # Авторы приходят строкой "A;B;C"
        names = [a.strip() for a in authors_raw.split(";") if a.strip()]
        for name in names:
            author, _ = Author.objects.get_or_create(name=name)
            book.authors.add(author)

    messages.success(request, f"Добавлено: {book.title}")
    return redirect("book_detail", pk=book.pk)


@login_required
@require_POST
def library_add(request, pk: int):
    book = get_object_or_404(Book, pk=pk)
    status = request.POST.get("status") or "wishlist"
    if status not in {"wishlist", "reading", "finished"}:
        status = "wishlist"

    obj, created = UserLibrary.objects.get_or_create(user=request.user, book=book)
    obj.status = status
    if status == "finished":
        obj.progress_percent = 100
    obj.save()

    messages.success(request, "Книга добавлена в твою библиотеку ✅" if created else "Обновлено ✅")
    return redirect("book_detail", pk=book.pk)


@login_required
def my_library(request):
    status = request.GET.get("status") or "wishlist"
    if status not in {"wishlist", "reading", "finished"}:
        status = "wishlist"

    items = (
        UserLibrary.objects.select_related("book")
        .filter(user=request.user, status=status)
        .order_by("-updated_at")
    )
    return render(request, "core/my_library.html", {"items": items, "status": status})


@login_required
@require_POST
def update_progress(request, pk: int):
    item = get_object_or_404(UserLibrary, user=request.user, book_id=pk)
    p_raw = (request.POST.get("progress") or "").strip()
    if p_raw.isdigit():
        p = int(p_raw)
        p = max(0, min(100, p))
        item.progress_percent = p
        if p == 100:
            item.status = "finished"
        item.save()
        messages.success(request, "Прогресс обновлён ✅")
    return redirect("my_library")


def _paginate_text(text: str, page_size: int = 1200) -> list[str]:
    """
    Very simple character-based pagination. This keeps logic in one place
    so we can later swap it for a smarter word/paragraph paginator.
    """
    pages: list[str] = []
    start = 0
    length = len(text)
    while start < length:
        end = min(start + page_size, length)
        pages.append(text[start:end])
        start = end
    return pages or [""]


@login_required
def read_book(request, pk: int):
    book = get_object_or_404(Book, pk=pk)

    # Access control: paid books only for purchasers
    if not book.is_free:
        has_purchase = Purchase.objects.filter(
            user=request.user,
            book=book,
            status=Purchase.Status.COMPLETED,
        ).exists()
        if not has_purchase:
            messages.error(request, "Эта книга доступна только после покупки.")
            return redirect("book_detail", pk=book.pk)

    chapters = list(BookChapter.objects.filter(book=book).order_by("order"))
    if not chapters:
        messages.info(request, "Для этой книги ещё не добавлено содержимое.")
        return redirect("book_detail", pk=book.pk)

    # Ensure pages exist for this book (auto-generate once if missing)
    pages_qs = BookPage.objects.filter(book=book).select_related("chapter").order_by(
        "number"
    )
    total_pages = pages_qs.count()
    if total_pages == 0:
        generate_pages_for_book(book)
        pages_qs = BookPage.objects.filter(book=book).select_related(
            "chapter"
        ).order_by("number")
        total_pages = pages_qs.count()
        if total_pages == 0:
            messages.info(
                request,
                "Для этой книги не удалось сгенерировать страницы. "
                "Администратору нужно выполнить команду generate_book_pages.",
            )
            return redirect("book_detail", pk=book.pk)

    # Determine current page number (1-based)
    page_param = request.GET.get("page")
    if page_param:
        try:
            page_number = int(page_param)
        except ValueError:
            page_number = 1
    else:
        progress = (
            ReadingProgress.objects.select_related("page")
            .filter(user=request.user, book=book, page__isnull=False)
            .first()
        )
        if progress and progress.page:
            page_number = progress.page.number
        else:
            page_number = 1

    page_number = max(1, min(page_number, total_pages))
    current_page = pages_qs.get(number=page_number)

    # Map chapters to their first page for table of contents
    first_pages_by_chapter_id = {
        p.chapter_id: p.number
        for p in BookPage.objects.filter(book=book, chapter_page_index=1)
    }
    for ch in chapters:
        ch.first_page_number = first_pages_by_chapter_id.get(ch.id)

    # Save detailed progress and approximate percent into UserLibrary
    ReadingProgress.objects.update_or_create(
        user=request.user,
        book=book,
        defaults={
            "chapter": current_page.chapter,
            "page_index": current_page.chapter_page_index,
            "page": current_page,
            "updated_at": timezone.now(),
        },
    )

    percent = int((page_number / total_pages) * 100)
    percent = max(0, min(100, percent))

    lib_entry, _ = UserLibrary.objects.get_or_create(
        user=request.user,
        book=book,
        defaults={"status": UserLibrary.Status.READING},
    )
    lib_entry.status = (
        UserLibrary.Status.FINISHED if percent == 100 else UserLibrary.Status.READING
    )
    lib_entry.progress_percent = percent
    lib_entry.save(update_fields=["status", "progress_percent", "updated_at"])

    context = {
        "book": book,
        "page": current_page,
        "page_number": page_number,
        "total_pages": total_pages,
        "chapters": chapters,
    }
    return render(request, "core/reader.html", context)