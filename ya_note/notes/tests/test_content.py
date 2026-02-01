from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from notes.models import Note

User = get_user_model()


class TestContent(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create_user(
            username='author', password='password123'
        )
        cls.another_user = User.objects.create_user(
            username='another', password='password123'
        )

        # Создаем заметки для разных пользователей
        cls.note1 = Note.objects.create(
            title='Заметка автора',
            text='Текст заметки автора',
            slug='author-note',
            author=cls.author
        )
        cls.note2 = Note.objects.create(
            title='Заметка другого пользователя',
            text='Текст заметки другого пользователя',
            slug='another-note',
            author=cls.another_user
        )
        cls.note3 = Note.objects.create(
            title='Еще одна заметка автора',
            text='Другой текст заметки автора',
            slug='author-note2',
            author=cls.author
        )

    def test_note_in_object_list(self):
        """отдельная заметка передаётся на страницу со списком заметок
        в списке object_list в словаре context.
        """
        self.client.login(username='author', password='password123')
        url = reverse('notes:list')
        response = self.client.get(url)
        self.assertIn(self.note1, response.context['object_list'])
        self.assertIn(self.note3, response.context['object_list'])
        self.assertNotIn(self.note2, response.context['object_list'])

    def test_user_notes_isolation(self):
        """в список заметок одного пользователя не попадают
        заметки другого пользователя.
        """
        # Автор видит только свои заметки
        self.client.login(username='author', password='password123')
        response = self.client.get(reverse('notes:list'))
        author_notes = response.context['object_list']
        self.assertEqual(len(author_notes), 2)
        self.assertIn(self.note1, author_notes)
        self.assertIn(self.note3, author_notes)
        self.assertNotIn(self.note2, author_notes)

        # Другой пользователь видит только свои заметки
        self.client.login(username='another', password='password123')
        response = self.client.get(reverse('notes:list'))
        another_notes = response.context['object_list']
        self.assertEqual(len(another_notes), 1)
        self.assertIn(self.note2, another_notes)
        self.assertNotIn(self.note1, another_notes)
        self.assertNotIn(self.note3, another_notes)

    def test_forms_on_pages(self):
        """На страницы создания и редактирования заметки передаются формы."""
        self.client.login(username='author', password='password123')

        # Страница создания заметки
        response = self.client.get(reverse('notes:add'))
        self.assertIn('form', response.context)

        # Страница редактирования заметки
        response = self.client.get(
            reverse('notes:edit', args=(self.note1.slug,))
        )
        self.assertIn('form', response.context)
