from http import HTTPStatus

from notes.forms import WARNING
from notes.models import Note
from notes.tests.base import BaseTestCase
from pytils.translit import slugify


class TestLogic(BaseTestCase):
    def test_authenticated_user_can_create_note(self):
        """Залогиненный пользователь может создать заметку."""
        Note.objects.all().delete()

        data = {
            "title": "Новая заметка",
            "text": "Текст новой заметки",
            "slug": "new-note",
        }
        response = self.author_client.post(self.add_url, data)

        self.assertRedirects(response, self.success_url)
        self.assertEqual(Note.objects.count(), 1)

        note = Note.objects.get()
        self.assertEqual(note.title, data["title"])
        self.assertEqual(note.text, data["text"])
        self.assertEqual(note.slug, data["slug"])
        self.assertEqual(note.author, self.author)

    def test_anonymous_user_cannot_create_note(self):
        """Анонимный пользователь не может создать заметку."""
        initial_count = Note.objects.count()
        data = {
            "title": "Новая заметка",
            "text": "Текст новой заметки",
            "slug": "new-note",
        }
        response = self.client.post(self.add_url, data)

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(Note.objects.count(), initial_count)

    def test_unique_slug_constraint(self):
        """Невозможно создать две заметки с одинаковым slug."""
        initial_count = Note.objects.count()
        data = {
            "title": "Вторая заметка",
            "text": "Текст второй заметки",
            "slug": self.note.slug,
        }
        response = self.author_client.post(self.add_url, data)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertIn("form", response.context)

        # Проверяем ошибки формы
        form = response.context["form"]
        self.assertTrue(form.errors)
        self.assertIn("slug", form.errors)
        errors = form.errors["slug"]
        self.assertTrue(any(WARNING in str(error) for error in errors))

        # Проверяем, что новая заметка не создалась
        self.assertEqual(Note.objects.count(), initial_count)

    def test_auto_slug_generation(self):
        """Если при создании заметки не заполнен slug,
        он формируется автоматически.
        """
        Note.objects.all().delete()

        title = "Заметка с автоматическим slug"
        data = {
            "title": title,
            "text": "Текст заметки",
        }
        response = self.author_client.post(self.add_url, data)

        self.assertRedirects(response, self.success_url)
        self.assertEqual(Note.objects.count(), 1)

        note = Note.objects.get()
        expected_slug = slugify(title)
        self.assertEqual(note.slug, expected_slug)
        self.assertEqual(note.title, data["title"])
        self.assertEqual(note.text, data["text"])
        self.assertEqual(note.author, self.author)

    def test_user_can_edit_own_notes(self):
        """Пользователь может редактировать свои заметки."""
        edit_data = {
            "title": "Обновленная заметка",
            "text": "Обновленный текст",
            "slug": "updated-note",
        }
        response = self.author_client.post(self.edit_url, edit_data)

        self.assertRedirects(response, self.success_url)

        note = Note.objects.get(pk=self.note.id)
        self.assertEqual(note.title, edit_data["title"])
        self.assertEqual(note.text, edit_data["text"])
        self.assertEqual(note.slug, edit_data["slug"])
        self.assertEqual(note.author, self.note.author)

    def test_user_can_delete_own_notes(self):
        """Пользователь может удалять свои заметки."""
        note_id = self.note.id
        response = self.author_client.post(self.delete_url)

        self.assertRedirects(response, self.success_url)
        self.assertFalse(Note.objects.filter(pk=note_id).exists())

    def test_user_cannot_edit_other_notes(self):
        """Пользователь не может редактировать чужие заметки."""
        initial_count = Note.objects.count()
        edit_data = {
            "title": "Взломанная заметка",
            "text": "Взломанный текст",
            "slug": "hacked-note",
        }

        response = self.author_client.post(self.foreign_edit_url, edit_data)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

        # Проверяем, что заметка не изменилась
        note = Note.objects.get(pk=self.another_note.id)
        self.assertEqual(note.title, self.another_note.title)
        self.assertEqual(note.text, self.another_note.text)
        self.assertEqual(note.slug, self.another_note.slug)
        self.assertEqual(note.author, self.another_note.author)
        self.assertEqual(Note.objects.count(), initial_count)

    def test_user_cannot_delete_other_notes(self):
        """Пользователь не может удалять чужие заметки."""
        initial_count = Note.objects.count()
        note_id = self.another_note.id

        response = self.author_client.post(self.foreign_delete_url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertEqual(Note.objects.count(), initial_count)
        self.assertTrue(Note.objects.filter(pk=note_id).exists())
