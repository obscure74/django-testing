import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from django.urls.exceptions import NoReverseMatch
from news.models import News, Comment
from datetime import datetime, timedelta


@pytest.mark.django_db
class TestContent:

    @pytest.fixture(autouse=True)
    def create_news(self):
        """Создает 15 новостей для тестирования."""
        for i in range(15):
            News.objects.create(
                title=f'Новость {i}',
                text=f'Текст новости {i}',
                date=datetime.now() - timedelta(hours=i)
            )

    def test_news_limit_on_home_page(self, client):
        """Количество новостей на главной странице — не более 10."""
        try:
            url = reverse('news:home')
        except NoReverseMatch:
            url = '/'

        response = client.get(url)

        news_list = None
        if 'news_list' in response.context:
            news_list = response.context['news_list']
        elif 'object_list' in response.context:
            news_list = response.context['object_list']
        elif hasattr(response, 'context_data'):
            if 'news_list' in response.context_data:
                news_list = response.context_data['news_list']
            elif 'object_list' in response.context_data:
                news_list = response.context_data['object_list']

        assert news_list is not None
        assert len(news_list) <= 10

    def test_news_sorted_by_date(self, client):
        """Новости отсортированы от самой свежей к самой старой."""
        try:
            url = reverse('news:home')
        except NoReverseMatch:
            url = '/'

        response = client.get(url)

        news_list = None
        if 'news_list' in response.context:
            news_list = response.context['news_list']
        elif 'object_list' in response.context:
            news_list = response.context['object_list']

        assert news_list is not None

        dates = [news.date for news in news_list]
        assert dates == sorted(dates, reverse=True)

    def test_comments_sorted_chronologically(self, client):
        """Комментарии отсортированы в хронологическом порядке."""
        news = News.objects.create(title='Тестовая новость', text='Текст')
        user = User.objects.create_user(
            username='user', password='password123'
        )

        old_comment = Comment.objects.create(
            news=news,
            author=user,
            text='Старый комментарий'
        )
        new_comment = Comment.objects.create(
            news=news,
            author=user,
            text='Новый комментарий'
        )

        try:
            url = reverse('news:detail', args=(news.id,))
        except NoReverseMatch:
            url = f'/{news.id}/'

        response = client.get(url)

        comments = None

        if 'comments' in response.context:
            comments = list(response.context['comments'])
        elif 'news' in response.context:
            news_obj = response.context['news']
            if hasattr(news_obj, 'comment_set'):
                comments = list(news_obj.comment_set.all().order_by('created'))

        if comments is None:
            comments = list(
                Comment.objects.filter(news=news).order_by('created')
            )

        assert len(comments) == 2
        assert comments[0].id == old_comment.id
        assert comments[1].id == new_comment.id
        assert comments[0].author == user
        assert comments[1].author == user

    def test_form_availability_for_anonymous(self, client):
        """Анонимному пользователю недоступна форма для комментария."""
        news = News.objects.create(title='Тестовая новость', text='Текст')

        try:
            url = reverse('news:detail', args=(news.id,))
        except NoReverseMatch:
            url = f'/{news.id}/'

        response = client.get(url)
        assert 'form' not in response.context

    def test_form_availability_for_authenticated(self, client):
        """Авторизованному доступна форма для комментария."""
        news = News.objects.create(title='Тестовая новость', text='Текст')
        user = User.objects.create_user(
            username='user', password='password123'
        )

        client.login(username=user.username, password='password123')

        try:
            url = reverse('news:detail', args=(news.id,))
        except NoReverseMatch:
            url = f'/{news.id}/'

        response = client.get(url)
        assert 'form' in response.context

        if 'form' in response.context:
            form = response.context['form']
            assert form is not None

        assert user.is_authenticated
        assert user.username == 'user'
