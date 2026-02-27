from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.db.models import Q  
from core.management.commands.generate_book_pages import generate_pages_for_book
import requests
from .models import Book, Author, BookChapter
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

from .management.commands.generate_book_pages import generate_pages_for_book

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
    query = (request.GET.get("q") or "").strip()
    
    if query:
        books = Book.objects.filter(Q(title__icontains=query) | Q(description__icontains=query))
    else:
        books = Book.objects.all()

    continue_item = _get_continue_reading(request.user)

    return render(
        request,
        "core/book_list.html",
        {
            "books": books,
            "q": query,
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
    title = request.POST.get("title", "").strip()
    source_id = request.POST.get("source_id", "").strip() 
    
    book, created = Book.objects.get_or_create(
        source_id=source_id,
        defaults={'title': title, 'source': 'openlibrary'}
    )


    if not book.chapters.exists():
        dummy_text = (
            f"Это начало реальной книги {title}. " + 
            "Тут идет очень много текста... " * 500 
        )
        BookChapter.objects.create(book=book, order=1, title="Глава 1", content=dummy_text)
        
        generate_pages_for_book(book)
    # 

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


def auto_fetch_text(book_title):
    real_content = f"Глава 1. Начало истории {book_title}.\n\n"
    long_text = "Далеко-далеко за словесными горами в стране гласных и согласных живут рыбные тексты. " * 1000
    return real_content + long_text
@login_required
def read_book(request, pk):
    book = get_object_or_404(Book, pk=pk)
    
    if not book.chapters.exists():
        text = auto_fetch_text(book.title)
        if text:
            chapter = BookChapter.objects.create(
                book=book, 
                title="Автозагрузка", 
                content=text, 
                order=1
            )
            generate_pages_for_book(book)
    
    page_number = request.GET.get('page', 1)
    page = BookPage.objects.filter(book=book, number=page_number).first()
    
    return render(request, 'core/reader.html', {
        'book': book,
        'page': page,
        'page_number': int(page_number),
        'total_pages': BookPage.objects.filter(book=book).count()
    })