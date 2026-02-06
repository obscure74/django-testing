from notes.forms import NoteForm
from notes.tests.base import BaseTestCase


class TestContent(BaseTestCase):
    def test_note_in_object_list(self):
        """Отдельная заметка передаётся на страницу со списком заметок."""
        response = self.author_client.get(self.list_url)
        object_list = response.context["object_list"]

        # Автор видит свою заметку
        self.assertIn(self.note, object_list)
        # Автор не видит чужую заметку
        self.assertNotIn(self.another_note, object_list)

    def test_user_notes_isolation(self):
        """В список заметок одного пользователя не попадают заметки другого."""
        # Автор видит только свои заметки
        response = self.author_client.get(self.list_url)
        author_notes = response.context["object_list"]

        # Проверяем, что есть заметки автора и нет чужих
        self.assertIn(self.note, author_notes)
        self.assertNotIn(self.another_note, author_notes)

        # Другой пользователь видит только свои заметки
        response = self.another_client.get(self.list_url)
        another_notes = response.context["object_list"]

        self.assertIn(self.another_note, another_notes)
        self.assertNotIn(self.note, another_notes)

    def test_forms_on_pages(self):
        """На страницы создания и редактирования заметки передаются формы."""
        with self.subTest("Страница создания заметки"):
            response = self.author_client.get(self.add_url)
            self.assertIn("form", response.context)
            form = response.context["form"]
            self.assertIsInstance(form, NoteForm)

        with self.subTest("Страница редактирования заметки"):
            response = self.author_client.get(self.edit_url)
            self.assertIn("form", response.context)
            form = response.context["form"]
            self.assertIsInstance(form, NoteForm)
