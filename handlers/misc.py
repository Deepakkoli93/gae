#!/usr/bin/env python

from google.appengine.ext.webapp import template
from google.appengine.ext import ndb
from google.appengine.api import mail
import cgi


import logging
import os.path
import webapp2
import models
from webapp2_extras import auth
from webapp2_extras import sessions

from webapp2_extras.auth import InvalidAuthIdError
from webapp2_extras.auth import InvalidPasswordError

current_sem = 1
registration_open = True

def user_required(handler):
  """
    Decorator that checks if there's a user associated with the current session.
    Will also fail if there's no session present.
  """
  def check_login(self, *args, **kwargs):
    auth = self.auth
    if not auth.get_user_by_session():
      self.redirect(self.uri_for('login'), abort=True)
    else:
      return handler(self, *args, **kwargs)

  return check_login

def admin_required(handler):
  """
    Decorator that checks if there's a user associated with the current session.
    Will also fail if there's no session present.
  """
  def check_login(self, *args, **kwargs):
    auth = self.auth.get_user_by_session()
    if not auth or auth['role']!='admin':
      self.redirect(self.uri_for('login'), abort=True)
    else:
      return handler(self, *args, **kwargs)

  return check_login

def faculty_required(handler):
  """
    Decorator that checks if there's a user associated with the current session.
    Will also fail if there's no session present.
  """
  def check_login(self, *args, **kwargs):
    auth = self.auth.get_user_by_session()
    if not auth or auth['role']!='faculty':
      self.redirect(self.uri_for('login'), abort=True)
    else:
      return handler(self, *args, **kwargs)

  return check_login

class BaseHandler(webapp2.RequestHandler):
  @webapp2.cached_property
  def auth(self):
    """Shortcut to access the auth instance as a property."""
    return auth.get_auth()

  @webapp2.cached_property
  def user_info(self):
    """Shortcut to access a subset of the user attributes that are stored
    in the session.

    The list of attributes to store in the session is specified in
      config['webapp2_extras.auth']['user_attributes'].
    :returns
      A dictionary with most user information
    """
    return self.auth.get_user_by_session()

  @webapp2.cached_property
  def user(self):
    """Shortcut to access the current logged in user.

    Unlike user_info, it fetches information from the persistence layer and
    returns an instance of the underlying model.

    :returns
      The instance of the user model associated to the logged in user.
    """
    u = self.user_info
    return self.user_model.get_by_id(u['user_id']) if u else None

  @webapp2.cached_property
  def user_model(self):
    """Returns the implementation of the user model.

    It is consistent with config['webapp2_extras.auth']['user_model'], if set.
    """    
    return self.auth.store.user_model

  @webapp2.cached_property
  def session(self):
      """Shortcut to access the current session."""
      return self.session_store.get_session(backend="datastore")

  def render_template(self, view_filename, params=None):
    if not params:
      params = {}
    user = self.user_info
    params['user'] = user
    path = os.path.join(os.path.dirname(__file__),'..', 'templates', view_filename)
    self.response.out.write(template.render(path, params))

  def display_message(self, message, role="admin"):
    """Utility function to display a template with a simple message."""
    params = {
      'message': message
    }
    if(role=="faculty"):
      self.render_template('faculty/message.html',params)
    elif(role=="student"):
      self.render_template('student/message.html',params)
    else:
      self.render_template('message.html', params)

  def display_popup(self, params):
    #params = {"message":message}
    self.render_template('popup.html',params)


  # this is needed for webapp2 sessions to work
  def dispatch(self):
      # Get a session store for this request.
      self.session_store = sessions.get_store(request=self.request)

      try:
          # Dispatch the request.
          webapp2.RequestHandler.dispatch(self)
      finally:
          # Save all sessions.
          self.session_store.save_sessions(self.response)

class MainHandler(BaseHandler):
  def get(self):
    self.render_template('main.html')


class ForgotPasswordHandler(BaseHandler):
  def get(self):
    self._serve_page()

  def post(self):
    username = self.request.get('username')

    user = self.user_model.get_by_auth_id(username)
    if not user:
      logging.info('Could not find any user entry for username %s', username)
      self._serve_page(not_found=True)
      return

    user_id = user.get_id()
    email = user.email_address
    token = self.user_model.create_signup_token(user_id)

    verification_url = self.uri_for('verification', type='p', user_id=user_id,
      signup_token=token, _full=True)

    msg = 'Send an email to user in order to reset their password. \
          They will be able to do so by visiting <a href="{url}">{url}</a>'

    sender_address = "deepakkoli93@gmail.com"
    subject = "Change your password"
    body = """Thank you for creating an account! Please change your password by clicking on the link below:%s""" % verification_url
    mail.send_mail(sender_address, email, subject, body)
    self.redirect(self.uri_for('login'), abort=True)
    self.display_message(msg.format(url=verification_url))
  
  def _serve_page(self, not_found=False):
    username = self.request.get('username')
    params = {
      'username': username,
      'not_found': not_found
    }
    self.render_template('forgot.html', params)


class VerificationHandler(BaseHandler):
  def get(self, *args, **kwargs):
    user = None
    user_id = kwargs['user_id']
    signup_token = kwargs['signup_token']
    verification_type = kwargs['type']

    # it should be something more concise like
    # self.auth.get_user_by_token(user_id, signup_token)
    # unfortunately the auth interface does not (yet) allow to manipulate
    # signup tokens concisely
    user, ts = self.user_model.get_by_auth_token(int(user_id), signup_token,
      'signup')

    if not user:
      logging.info('Could not find any user with id "%s" signup token "%s"',
        user_id, signup_token)
      self.abort(404)
    
    # store user data in the session
    self.auth.set_session(self.auth.store.user_to_dict(user), remember=True)

    if verification_type == 'v':
      # remove signup token, we don't want users to come back with an old link
      self.user_model.delete_signup_token(user.get_id(), signup_token)

      if not user.verified:
        user.verified = True
        user.put()

      self.display_message('User email address has been verified.')
      return
    elif verification_type == 'p':
      # supply user to the page
      params = {
        'user': user,
        'token': signup_token
      }
      self.render_template('resetpassword.html', params)
    else:
      logging.info('verification type not supported')
      self.abort(404)

class SetPasswordHandler(BaseHandler):

  @user_required
  def post(self):
    password = self.request.get('password')
    old_token = self.request.get('t')

    if not password or password != self.request.get('confirm_password'):
      self.display_message('passwords do not match')
      return

    user = self.user
    user.set_password(password)
    user.put()

    # remove signup token, we don't want users to come back with an old link
    self.user_model.delete_signup_token(user.get_id(), old_token)
    
    self.display_message('Password updated')

class LoginHandler(BaseHandler):
  def get(self):
    self._serve_page()

  def post(self):
    username = self.request.get('username')
    password = self.request.get('password')
    try:
      u = self.auth.get_user_by_password(username, password, remember=True,
        save_session=True)
      user_data = self.user
      logging.info('user data  is %s' %user_data)
      #self.display_message('Welcome %s' %u['name'] )
      #self.display_message('you are %s' %user_data.role)
      if(user_data.role=='admin'):
        self.redirect(self.uri_for('admin'))
      if(user_data.role=='student'):
        self.redirect(self.uri_for('student'))
      if(user_data.role=='faculty'):
        self.redirect(self.uri_for('faculty'))
        #self.render_template('admin.html',False)
      #if(u['role']=='student'):
       #self.display_message('you are a student')
      #self.redirect(self.uri_for('home'))

    except (InvalidAuthIdError, InvalidPasswordError) as e:
      logging.info('Login failed for user %s because of %s', username, type(e))
      self._serve_page(True)

  def _serve_page(self, failed=False):
    username = self.request.get('username')
    params = {
      'username': username,
      'failed': failed
    }
    self.render_template('login.html', params)



class LogoutHandler(BaseHandler):
  def get(self):
    self.auth.unset_session()
    self.redirect(self.uri_for('main'))

class AuthenticatedHandler(BaseHandler):
  @user_required
  def get(self):
    self.render_template('authenticated.html')

class GodmodeHandler(BaseHandler):
  @admin_required
  def get(self):
    stat = models.Registration_status(open=True, id="registration_status")
    stat.put()
    sem = models.Semester(semester = "I sem 2015-2016", id="current_sem")
    sem.put()
    self.display_message('registration status put as true and semester entity created')


config = {
  'webapp2_extras.auth': {
    'user_model': 'models.User',
    'user_attributes': ['name','role']
  },
  'webapp2_extras.sessions': {
    'secret_key': 'YOUR_SECRET_KEY'
  }
}

