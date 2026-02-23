from django.urls import path

from .views import (
    book_list,
    book_detail,
    import_search,
    import_add,
    my_library,
    library_add,
    update_progress,
    read_book,
)

urlpatterns = [
    path("", book_list, name="book_list"),
    path("books/<int:pk>/", book_detail, name="book_detail"),
    path("books/<int:pk>/read/", read_book, name="book_read"),

    path("import/", import_search, name="import_search"),
    path("import/add/", import_add, name="import_add"),

    path("me/library/", my_library, name="my_library"),
    path("books/<int:pk>/library/add/", library_add, name="library_add"),
    path("books/<int:pk>/library/progress/", update_progress, name="update_progress"),
]