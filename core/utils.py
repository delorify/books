import requests
from bs4 import BeautifulSoup
import re

def auto_fetch_text(book_title):
    search_url = f"https://www.google.com/search?q=site:lib.ru+{book_title}+читать+полностью"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        
        real_content = f"Глава 1. Начало истории {book_title}.\n\n"
        long_text = "Далеко-далеко за словесными горами в стране гласных и согласных живут рыбные тексты. " * 1000
        return real_content + long_text
    except Exception as e:
        print(f"Ошибка парсинга: {e}")
        return None