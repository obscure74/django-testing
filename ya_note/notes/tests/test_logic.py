from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from notes.models import Note
from pytils.translit import slugify

User = get_user_model()


class TestLogic(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create_user(
            username='author', password='password123'
        )
        cls.another_user = User.objects.create_user(
            username='another', password='password123'
        )

    def test_authenticated_user_can_create_note(self):
        """Залогиненный пользователь может создать заметку, а анонимный —
        не может.
        """
        self.client.login(username='author', password='password123')
        data = {
            'title': 'Новая заметка',
            'text': 'Текст новой заметки',
            'slug': 'new-note'
        }
        url = reverse('notes:add')
        response = self.client.post(url, data)
        self.assertRedirects(response, reverse('notes:success'))
        self.assertTrue(Note.objects.filter(slug='new-note').exists())

    def test_anonymous_user_cannot_create_note(self):
        """Анонимный пользователь не может создать заметку."""
        data = {
            'title': 'Новая заметка',
            'text': 'Текст новой заметки',
            'slug': 'new-note'
        }
        url = reverse('notes:add')
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Note.objects.exists())

    def test_unique_slug_constraint(self):
        """Невозможно создать две заметки с одинаковым slug."""
        self.client.login(username='author', password='password123')

        # Первая заметка
        data1 = {
            'title': 'Первая заметка',
            'text': 'Текст первой заметки',
            'slug': 'duplicate-slug'
        }
        response1 = self.client.post(reverse('notes:add'), data1)
        self.assertRedirects(response1, reverse('notes:success'))

        # Вторая заметка с тем же slug
        data2 = {
            'title': 'Вторая заметка',
            'text': 'Текст второй заметки',
            'slug': 'duplicate-slug'
        }
        response2 = self.client.post(reverse('notes:add'), data2)
        self.assertEqual(response2.status_code, 200)
        # Проверяем, что форма содержит ошибку в поле slug
        self.assertTrue('form' in response2.context)
        self.assertTrue('slug' in response2.context['form'].errors)

    def test_auto_slug_generation(self):
        """Если при создании заметки не заполнен slug, то он формируется
        автоматически, с помощью функции pytils.translit.slugify.
        """
        self.client.login(username='author', password='password123')
        title = 'Заметка с автоматическим slug'
        data = {
            'title': title,
            'text': 'Текст заметки',
            # slug не указываем
        }
        response = self.client.post(reverse('notes:add'), data)
        self.assertRedirects(response, reverse('notes:success'))

        note = Note.objects.get(title=title)
        expected_slug = slugify(title)
        self.assertEqual(note.slug, expected_slug)

    def test_user_can_edit_delete_own_notes(self):
        """Пользователь может редактировать и удалять свои заметки."""
        note = Note.objects.create(
            title='Моя заметка',
            text='Мой текст',
            slug='my-note',
            author=self.author
        )

        self.client.login(username='author', password='password123')

        # Редактирование
        edit_data = {
            'title': 'Обновленная заметка',
            'text': 'Обновленный текст',
            'slug': 'updated-note'
        }
        response = self.client.post(
            reverse('notes:edit', args=(note.slug,)), edit_data
        )
        self.assertRedirects(response, reverse('notes:success'))

        note.refresh_from_db()
        self.assertEqual(note.title, 'Обновленная заметка')
        self.assertEqual(note.slug, 'updated-note')

        # Удаление
        response = self.client.post(reverse('notes:delete', args=(note.slug,)))
        self.assertRedirects(response, reverse('notes:success'))
        self.assertFalse(Note.objects.filter(slug='updated-note').exists())

    def test_user_cannot_edit_delete_other_notes(self):
        """Пользователь не может редактировать или удалять чужие заметки."""
        note = Note.objects.create(
            title='Чужая заметка',
            text='Чужой текст',
            slug='foreign-note',
            author=self.another_user
        )

        self.client.login(username='author', password='password123')

        # Попытка редактирования
        edit_data = {
            'title': 'Взломанная заметка',
            'text': 'Взломанный текст',
            'slug': 'hacked-note'
        }
        response = self.client.post(
            reverse('notes:edit', args=(note.slug,)), edit_data
        )
        self.assertEqual(response.status_code, 404)

        # Попытка удаления
        response = self.client.post(reverse('notes:delete', args=(note.slug,)))
        self.assertEqual(response.status_code, 404)

        # Заметка осталась неизменной
        note.refresh_from_db()
        self.assertEqual(note.title, 'Чужая заметка')
        self.assertTrue(Note.objects.filter(slug='foreign-note').exists())
