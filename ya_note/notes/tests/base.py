from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from notes.models import Note

User = get_user_model()


class BaseTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Создаем пользователей
        cls.author = User.objects.create_user(
            username="author", password="password123"
        )
        cls.reader = User.objects.create_user(
            username="reader", password="password123"
        )
        cls.another_user = User.objects.create_user(
            username="another", password="password123"
        )

        # Создаем заметки
        cls.note = Note.objects.create(
            title="Тестовая заметка",
            text="Текст заметки",
            slug="test-note",
            author=cls.author,
        )
        cls.another_note = Note.objects.create(
            title="Чужая заметка",
            text="Текст чужой заметки",
            slug="foreign-note",
            author=cls.another_user,
        )

        # Рассчитываем URL-адреса заранее
        cls.home_url = reverse("notes:home")
        cls.list_url = reverse("notes:list")
        cls.success_url = reverse("notes:success")
        cls.add_url = reverse("notes:add")
        cls.detail_url = reverse("notes:detail", args=(cls.note.slug,))
        cls.edit_url = reverse("notes:edit", args=(cls.note.slug,))
        cls.delete_url = reverse("notes:delete", args=(cls.note.slug,))
        cls.login_url = reverse("users:login")
        cls.logout_url = reverse("users:logout")
        cls.signup_url = reverse("users:signup")

        # Создаем клиенты с авторизованными пользователями
        cls.author_client = cls._create_client(cls.author)
        cls.reader_client = cls._create_client(cls.reader)
        cls.another_client = cls._create_client(cls.another_user)

    @classmethod
    def _create_client(cls, user):
        """Создает клиент с авторизованным пользователем."""
        from django.test import Client

        client = Client()
        client.login(username=user.username, password="password123")
        return client
