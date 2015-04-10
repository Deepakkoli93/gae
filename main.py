#!/usr/bin/env python

from google.appengine.ext.webapp import template
from google.appengine.ext import ndb
from google.appengine.api import mail


import logging
import os.path
import webapp2
import models

from webapp2_extras import auth
from webapp2_extras import sessions

from webapp2_extras.auth import InvalidAuthIdError
from webapp2_extras.auth import InvalidPasswordError

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
    path = os.path.join(os.path.dirname(__file__), 'views', view_filename)
    self.response.out.write(template.render(path, params))

  def display_message(self, message):
    """Utility function to display a template with a simple message."""
    params = {
      'message': message
    }
    self.render_template('message.html', params)

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

class SignupHandler(BaseHandler):
 # @admin_required
  def get(self):
    self.render_template('signup.html')

  def post(self):
    user_name = self.request.get('username')
    email = self.request.get('email')
    name = self.request.get('name')
    password = self.request.get('password')
    last_name = self.request.get('lastname')
    department = self.request.get('department')
    role = self.request.get('role')
    logging.info('role of the student is %s' %role)

    dep = models.Department.get_by_id(department)
    if dep==None:
      self.display_message('department does not exist, user not created')
      return

    unique_properties = ['email_address']
    user_data = self.user_model.create_user(user_name,
      unique_properties,
      email_address=email, name=name, password_raw=password,
      last_name=last_name,department=department, role=role,verified=False)
    if not user_data[0]: #user_data is a tuple
      self.display_message('Unable to create user for email %s because of \
        duplicate keys %s' % (user_name, user_data[1]))
      return
    
    user = user_data[1]
    if(role=="student"):
      stu = models.Student(student=user.key, department=department, credits=10, id=user_name)
      stu.put()

    if(role=="faculty"):
      fac = models.Faculty(faculty=user.key, id=user_name)
      fac.put()

    user_id = user.get_id()

    token = self.user_model.create_signup_token(user_id)

    verification_url = self.uri_for('verification', type='v', user_id=user_id,
      signup_token=token, _full=True)

    msg = 'Send an email to user in order to verify their address. \
          They will be able to do so by visiting <a href="{url}">{url}</a>'

    self.display_message(msg.format(url=verification_url))

    sender_address = "deepakkoli93@gmail.com"
    subject = "Confirm your registration"
    body = """Thank you for creating an account! Please confirm your email address by clicking on the link below:%s""" % verification_url
    mail.send_mail(sender_address, email, subject, body)

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
    token = self.user_model.create_signup_token(user_id)

    verification_url = self.uri_for('verification', type='p', user_id=user_id,
      signup_token=token, _full=True)

    msg = 'Send an email to user in order to reset their password. \
          They will be able to do so by visiting <a href="{url}">{url}</a>'

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
      self.display_message('Welcome %s' %u['name'] )
      self.display_message('you are %s' %user_data.role)
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

class AdminHandler(BaseHandler):
  @user_required
  def get(self):
    self._serve_page()

  def _serve_page(self, ):
    #self.display_message(self.user)
    self.render_template('admin.html')

class addDepartmentHandler(BaseHandler):
  @admin_required
  def get(self):
    self.render_template('addDepartment.html')

  def post(self):
    dep_id = self.request.get('dep_id')
    name = self.request.get('name')
    hod = self.request.get('hod')

    valid_hod  = models.Faculty.get_by_id(hod)
    dep = models.Department.get_by_id(dep_id)
    if valid_hod==None:
      self.display_message("hod does not exist")
    else:
      if dep==None:
        dep = self.models.Department(dep_id=dep_id, name=name, hod=valid_hod.key, id=dep_id)
        dep.put()
      else:
        dep.name = name
        dep.hod = valid_hod.key
        dep.put()

class addCourseHandler(BaseHandler):
  @admin_required
  def get(self):
    self.render_template('addCourse.html')

  def get(post):
    course_id = self.request.get('course_id')
    name = self.request.get('name')
    coordinator = self.request.get('coordinator')
    department = self.request.get('department')
    floated = self.request.get('floated')
    prereq = self.request.get('prereq')

class LogoutHandler(BaseHandler):
  def get(self):
    self.auth.unset_session()
    self.redirect(self.uri_for('main'))

class AuthenticatedHandler(BaseHandler):
  @user_required
  def get(self):
    self.render_template('authenticated.html')

class removeUserHandler(BaseHandler):
  @admin_required
  def get(self):
    pass

  def post(self):
    #username = self.request.get('username')
    #uid = models.User.get_by_id(username)
    #uid.delete()
    #self.display_message(uid)
    #TODO remove user?
    pass
class StudentHandler(BaseHandler):
  @user_required
  def get(self):
    self.render_template('student/student.html')

class FacultyHandler(BaseHandler):
  @faculty_required
  def get(self):
    self.render_template('faculty/faculty.html')

class FacultyInfoHandler(BaseHandler):
  @faculty_required
  def get(self):
    params = {
    'user_data' : self.user,
    'faculty_data' : models.Student.get_by_id(self.user.email_address)
    }
    self.render_template('faculty/info.html',params)

class FacultyCoursesHandler(BaseHandler):
  @faculty_required
  def get(self):
    self.render_template('faculty/courses.html')

class FacultyRequestsHandler(BaseHandler):
  @faculty_required
  def get(self):
    self.render_template('faculty/requests.html')

class StudentInfoHandler(BaseHandler):
  @user_required
  def get(self):
    params = {
    'user_data' : self.user,
    'student_data' : models.Student.get_by_id(self.user.email_address)
    }
    self.render_template('student/info.html', params)

class CartHandler(BaseHandler):
  @user_required
  def get(self):
    self.render_template('student/cart.html')
config = {
  'webapp2_extras.auth': {
    'user_model': 'models.User',
    'user_attributes': ['name','role']
  },
  'webapp2_extras.sessions': {
    'secret_key': 'YOUR_SECRET_KEY'
  }
}

app = webapp2.WSGIApplication([
    webapp2.Route('/', MainHandler, name='main'),
    webapp2.Route('/signup', SignupHandler),
    webapp2.Route('/<type:v|p>/<user_id:\d+>-<signup_token:.+>',
      handler=VerificationHandler, name='verification'),
    webapp2.Route('/password', SetPasswordHandler),
    webapp2.Route('/login', LoginHandler, name='login'),
    webapp2.Route('/logout', LogoutHandler, name='logout'),
    webapp2.Route('/forgot', ForgotPasswordHandler, name='forgot'),
    webapp2.Route('/authenticated', AuthenticatedHandler, name='authenticated'),
    webapp2.Route('/admin', AdminHandler, name='admin'),
    webapp2.Route('/removeUser', removeUserHandler),
    webapp2.Route('/student', StudentHandler, name='student'),
    webapp2.Route('/faculty', FacultyHandler, name='faculty'),
    webapp2.Route('/faculty/info', FacultyInfoHandler),
    webapp2.Route('/faculty/courses', FacultyCoursesHandler),
    webapp2.Route('/faculty/requests', FacultyRequestsHandler),
    webapp2.Route('/student/info', StudentInfoHandler),
    webapp2.Route('/student/cart', CartHandler),
    webapp2.Route('/addDepartment', addDepartmentHandler),
    webapp2.Route('/addCourse', addCourseHandler)
], debug=True, config=config)

logging.getLogger().setLevel(logging.DEBUG)
