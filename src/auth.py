from bs4 import BeautifulSoup
import requests


class AuthManager:
  """Gerencia a autenticação na plataforma Invision Power Suite (encontrei.info)

  via requisições HTTP rápidas, extraindo os cookies da sessão autenticada.
  """

  def __init__(
      self,
      email: str = '',
      password: str = '',
      base_url: str = 'https://encontrei.info/',
  ):
    self.email = email
    self.password = password
    self.base_url = base_url
    self.session = requests.Session()
    self.session.headers.update({
        'User-Agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            ' (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ),
        'Accept': (
            'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        ),
        'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
    })
    self.is_authenticated = False

  def login(self) -> bool:
    """Realiza o login via HTTP post utilizando as credenciais configuradas pelo usuário e retorna True caso bem-sucedido."""
    if not self.email or not self.password:
      print('Login não realizado: E-mail ou senha não foram preenchidos pelo usuário nas Configurações.')
      self.is_authenticated = False
      return False

    try:
      login_url = 'https://encontrei.info/login/'
      resp_get = self.session.get(login_url, timeout=15)
      soup = BeautifulSoup(resp_get.text, 'html.parser')
      login_form = soup.find('form')

      form_data = {
          'auth': self.email,
          'password': self.password,
          'remember_me': '1',
          '_processLogin': 'usernamepassword',
      }
      if login_form:
        for inp in login_form.find_all('input'):
          name = inp.get('name')
          if name and name not in form_data:
            form_data[name] = inp.get('value', '')

      post_url = (
          login_form.get('action')
          if login_form and login_form.get('action')
          else login_url
      )
      resp_post = self.session.post(post_url, data=form_data, timeout=20)
      # Se logou, 'memberID: 0' sai do escopo global de controle do IPS
      if (
          'memberID: 0' not in resp_post.text
          or len(self.session.cookies) > 2
      ):
        self.is_authenticated = True
        return True
      else:
        self.is_authenticated = False
        return False
    except Exception as e:
      print(f'Erro durante tentativa de login HTTP: {e}')
      self.is_authenticated = False
      return False

  def get_playwright_cookies(self, domain_override='encontrei.info') -> list:
    """Converte os cookies do Requests para a estrutura esperada pelo Playwright."""
    pw_cookies = []
    for cookie in self.session.cookies:
      dom = cookie.domain
      if not dom or dom == '':
        dom = domain_override
      if not dom.startswith('.'):
        dom = '.' + dom.lstrip('.')
      pw_cookies.append({
          'name': cookie.name,
          'value': cookie.value,
          'domain': dom,
          'path': '/',
      })
    return pw_cookies

  def get_session(self) -> requests.Session:
    return self.session
