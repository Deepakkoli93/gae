import time
import webapp2_extras.appengine.auth.models

from google.appengine.ext import ndb

from webapp2_extras import security

class User(webapp2_extras.appengine.auth.models.User):
  def set_password(self, raw_password):
    """Sets the password for the current user

    :param raw_password:
        The raw password which will be hashed and stored
    """
    self.password = security.generate_password_hash(raw_password, length=12)
  def set_email(self, email):
    self.email_address = email
  def set_name(self, name):
    self.name = name
  def set_lastname(self, lastname):
    self.last_name = lastname
  def set_department(self, department):
    self.department(department)
  @classmethod
  def get_by_auth_token(cls, user_id, token, subject='auth'):
    """Returns a user object based on a user ID and token.

    :param user_id:
        The user_id of the requesting user.
    :param token:
        The token string to be verified.
    :returns:
        A tuple ``(User, timestamp)``, with a user object and
        the token timestamp, or ``(None, None)`` if both were not found.
    """
    token_key = cls.token_model.get_key(user_id, subject, token)
    user_key = ndb.Key(cls, user_id)
    # Use get_multi() to save a RPC call.
    valid_token, user = ndb.get_multi([token_key, user_key])
    if valid_token and user:
        timestamp = int(time.mktime(valid_token.created.timetuple()))
        return user, timestamp

    return None, None



class Faculty(ndb.Model):
    """Models a  faculty with hod, courses, resume, webpage and a link to the user"""
    faculty = ndb.KeyProperty(kind = User)
    name = ndb.StringProperty()
    resume = ndb.BlobProperty()
    webpage = ndb.StringProperty()

class Department(ndb.Model):
  """Models a department with department id."""
  dep_id = ndb.StringProperty()
  name = ndb.StringProperty()
  hod = ndb.KeyProperty(kind = Faculty)

class AcademicHistory(ndb.Model):
  """Models the academic history of a student. It includes coures done,
  grade obtained in it and the semester"""
  course = ndb.StringProperty()
  grade = ndb.StringProperty()
  semester = ndb.StringProperty()

class Student(ndb.Model):
  """Models a student"""
  student = ndb.KeyProperty(kind = User)
  name = ndb.StringProperty()
  credits = ndb.FloatProperty()
  history = ndb.StructuredProperty(AcademicHistory, repeated = True)

class Course(ndb.Model):
    """Models a course"""
    course_id = ndb.StringProperty()
    name = ndb.StringProperty()
    description = ndb.StringProperty()
    coordinator = ndb.KeyProperty(kind = Faculty)
    department = ndb.KeyProperty(kind = Department)
    credits = ndb.FloatProperty()
    floated = ndb.BooleanProperty()
    prereq = ndb.KeyProperty(kind = 'Course', repeated = True)

class Registration(ndb.Model):
  """Models the registration status"""
  course = ndb.KeyProperty(kind = Course)
  student = ndb.KeyProperty(kind = Student)
  closed = ndb.BooleanProperty()
  
class Application(ndb.Model):
  """Models the credit relaxation(false) and course approval(true) requests"""
  app_type = ndb.BooleanProperty()
  student = ndb.KeyProperty(kind = Student)
  faculty = ndb.KeyProperty(kind = Faculty)
  course = ndb.KeyProperty(kind = Course)
  content = ndb.StringProperty()
  status = ndb.BooleanProperty()

class Resources(ndb.Model):
  resource_title = ndb.StringProperty()
  resource_key = ndb.BlobKeyProperty()

class Fac_Resources(ndb.Model):
  resource_title = ndb.StringProperty()
  resource_key = ndb.BlobKeyProperty()
  resource_type = ndb.BooleanProperty() # type = true if assignment, false if just a resource
  course = ndb.KeyProperty(kind = Course)
  
class Assignment(ndb.Model):
  resource_id = ndb.KeyProperty(kind = Fac_Resources)
  student = ndb.KeyProperty(kind = Student)
  resource_key = ndb.BlobKeyProperty()

class Registration_status(ndb.Model):
  """Models the status of registration"""
  open = ndb.BooleanProperty()


