from http import HTTPStatus

import pytest
from django.conf import settings
from news.forms import CommentForm

pytestmark = pytest.mark.django_db


class TestContent:
    def test_news_limit_on_home_page(self, client, many_news, home_url):
        """
        На главной странице показывается не более
        settings.NEWS_COUNT_ON_HOME_PAGE новостей.
        """
        response = client.get(home_url)
        assert response.status_code == HTTPStatus.OK

        news_list = response.context.get("object_list", [])
        assert news_list is not None
        assert len(news_list) == settings.NEWS_COUNT_ON_HOME_PAGE

    def test_news_sorted_by_date(self, client, many_news, home_url):
        """Новости отсортированы от самой свежей к самой старой."""
        response = client.get(home_url)
        assert response.status_code == HTTPStatus.OK

        news_list = response.context.get("object_list", [])
        dates = [n.date for n in news_list]
        assert dates == sorted(dates, reverse=True)

    def test_comments_sorted_chronologically(
        self, client, news, author, comments_factory, news_detail_url
    ):
        """Комментарии отсортированы по полю created (от старых к новым)."""
        comments_factory(count=5)
        response = client.get(news_detail_url)
        assert response.status_code == HTTPStatus.OK

        comments = []
        if "comments" in response.context:
            comments = list(response.context["comments"])
        elif "news" in response.context:
            news_obj = response.context["news"]
            comments = list(news_obj.comment_set.all())

        assert len(comments) >= 2
        dates = [c.created for c in comments]
        assert dates == sorted(dates)  # от старых к новым

    def test_form_availability_for_anonymous(self, client, news_detail_url):
        """Анонимному пользователю недоступна форма для комментария."""
        response = client.get(news_detail_url)
        assert response.status_code == HTTPStatus.OK
        assert "form" not in response.context

    def test_form_availability_for_authenticated(self, user_client, news_detail_url):
        """Авторизованному доступна форма для комментария и это CommentForm."""
        response = user_client.get(news_detail_url)
        assert response.status_code == HTTPStatus.OK
        assert "form" in response.context

        form = response.context["form"]
        assert form is not None
        assert isinstance(form, CommentForm)
