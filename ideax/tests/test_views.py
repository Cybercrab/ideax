from django.http.response import HttpResponseRedirect


class TestViews(object):
    def test_frontpage(self, client):
        response = client.get('/')
        body = response.content.decode('utf-8', 'strict')
        assert 'você tem um canal aberto para a inovação' in body

    def test_redirect_login(self, client):
        response = client.get('/idea/list')
        assert response.status_code == 302
        assert isinstance(response, HttpResponseRedirect)
        assert response.url == r'/accounts/login/?next=/idea/list'

    def test_idea_list(self, client, django_user_model):
        username, password = 'usuario', 'senha'
        django_user_model.objects.create_user(
          username=username,
          password=password,
          email='x@x.com')
        client.login(username=username, password=password)
        response = client.get('/idea/list')
        assert response.status_code == 200
        body = response.content.decode('utf-8', 'strict')
        assert 'Não existem ideias nesta etapa' in body
