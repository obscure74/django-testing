from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from notes.models import Note

User = get_user_model()


class TestRoutes(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create_user(
            username='author', password='password123'
        )
        cls.reader = User.objects.create_user(
            username='reader', password='password123'
        )
        cls.note = Note.objects.create(
            title='Тестовая заметка',
            text='Текст заметки',
            slug='test-note',
            author=cls.author
        )

    def test_home_page_anonymous_accessible(self):
        """Главная страница доступна анонимному пользователю."""
        url = reverse('notes:home')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_authenticated_user_pages_accessible(self):
        """Аутентифицированному пользователю доступна страница
        со списком заметок notes/,
        страница успешного добавления заметки done/,
        страница добавления новой заметки add/.
        """
        self.client.login(username='author', password='password123')
        urls = [
            reverse('notes:list'),        # /notes/
            reverse('notes:success'),     # /done/
            reverse('notes:add'),         # /add/
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)

    def test_note_pages_author_only(self):
        """Страницы отдельной заметки, удаления и редактирования заметки
        доступны только автору заметки.
        Если на эти страницы попытается зайти другой
        пользователь — вернётся ошибка 404.
        """
        # Автор может получить доступ
        self.client.login(username='author', password='password123')
        urls = [
            reverse('notes:detail', args=(self.note.slug,)),
            reverse('notes:edit', args=(self.note.slug,)),
            reverse('notes:delete', args=(self.note.slug,)),
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)

        # Другой пользователь получает 404
        self.client.login(username='reader', password='password123')
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 404)

    def test_anonymous_redirect_to_login(self):
        """При попытке перейти на страницу списка заметок, страницу успешного
        добавления записи, страницу добавления заметки, отдельной заметки,
        редактирования или удаления заметки анонимный пользователь
        перенаправляется на страницу логина.
        """
        urls = [
            reverse('notes:list'),
            reverse('notes:success'),
            reverse('notes:add'),
            reverse('notes:detail', args=(self.note.slug,)),
            reverse('notes:edit', args=(self.note.slug,)),
            reverse('notes:delete', args=(self.note.slug,))
        ]

        # Используем реальный URL из проверки
        login_url = reverse('users:login')  # /auth/login/

        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertRedirects(response, f'{login_url}?next={url}')

    def test_auth_pages_accessible(self):
        """Страницы регистрации пользователей, входа в учётную запись и выхода
        из неё доступны всем пользователям.
        """
        urls = [
            reverse('users:login'),    # /auth/login/
            reverse('users:logout'),   # /auth/logout/
            reverse('users:signup'),   # /auth/signup/
        ]

        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertIn(response.status_code, [200, 405])
