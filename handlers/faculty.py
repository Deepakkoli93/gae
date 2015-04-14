from misc import *

class FacultyHandler(BaseHandler):
  @faculty_required
  def get(self):
    self.render_template('faculty/faculty.html')

class FacultyInfoHandler(BaseHandler):
  @faculty_required
  def get(self):
    params = {
    'user_data' : self.user,
    'faculty_data' : models.Faculty.get_by_id(self.user.auth_ids[0])
    }
    self.render_template('faculty/info.html',params)
  def post(self):
    email = self.request.get('email')
    name = self.request.get('name')
    last_name = self.request.get('lastname')
    webpage = self.request.get('webpage')
    """ Change the fields ................................................................................................"""
    fac_user = models.Faculty.get_by_id(self.user.auth_ids[0])
    self.user.set_email(email)
    self.user.set_name(name)
    self.user.set_lastname(last_name)
    self.user.put()
    fac_user.webpage = webpage
    fac_user.put()
    self.display_message("information saved successfully","faculty")

class FacultyCoursesHandler(BaseHandler):
  @faculty_required
  def get(self):
    self.render_template('faculty/courses.html')

class FacultyRequestsHandler(BaseHandler):
  @faculty_required
  def get(self):
    self.render_template('faculty/requests.html')
