from django.contrib import admin
from .models import Book, Author, UserLibrary, Purchase


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    search_fields = ("name",)


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("title", "year", "is_paid", "price", "source", "created_at")
    search_fields = ("title", "source_id")
    list_filter = ("is_paid", "source", "created_at")
    autocomplete_fields = ("authors",)


@admin.register(UserLibrary)
class UserLibraryAdmin(admin.ModelAdmin):
    list_display = ("user", "book", "status", "progress_percent", "updated_at")
    list_filter = ("status",)
    search_fields = ("user__username", "book__title")


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ("user", "book", "amount", "created_at")
    search_fields = ("user__username", "book__title")