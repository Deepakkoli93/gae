from misc import *
from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.ext.webapp.util import run_wsgi_app

class FacultyHandler(BaseHandler):
  @faculty_required
  def get(self):
    course_list =list()
    fac = models.Faculty.get_by_id(self.user.auth_ids[0])
    course_query = models.Course.query(models.Course.coordinator==fac.key)
    courses = course_query.fetch(100)
    for course in courses:
      course_list.append(course)
    params = {
    'user_data' : self.user,
    'userid' : self.user.auth_ids[0],
    'faculty_data' : models.Faculty.get_by_id(self.user.auth_ids[0]),
    'courses':course_list
    }
    #logging.info(models.Student.get_by_id(self.user.auth_ids[0]))
    self.render_template('faculty/faculty.html',params)
        
  def post(self): # only called if you press one of the course buttons
    course_list = list()
    fac = models.Faculty.get_by_id(self.user.auth_ids[0])
    course_query = models.Course.query(models.Course.coordinator==fac.key)
    courses = course_query.fetch(100)
    for course in courses:
      course_list.append(course)
    for course in course_list:
      pressed = self.request.get(course.course_id)
      logging.info(pressed)
      if pressed:
          logging.info('if pressed')
          upload_url = blobstore.create_upload_url('/faculty/resource_upload')
          resources = models.Fac_Resources.query(models.Fac_Resources.course==course.key)
          params = {'course':course,'courses':course_list,"upload_url":upload_url,"resources":resources}
          self.render_template('faculty/courses.html',params)

class FacultyInfoHandler(BaseHandler):
  @faculty_required
  def get(self):
    course_list =list()
    fac = models.Faculty.get_by_id(self.user.auth_ids[0])
    course_query = models.Course.query(models.Course.coordinator==fac.key)
    courses = course_query.fetch(100)
    for course in courses:
      course_list.append(course)
    params = {
    'user_data' : self.user,
    'userid' : self.user.auth_ids[0],
    'faculty_data' : models.Faculty.get_by_id(self.user.auth_ids[0]),
    'courses':course_list
    }
    logging.info(models.Student.get_by_id(self.user.auth_ids[0]))
    self.render_template('faculty/info.html',params)
  def post(self):
    email = self.request.get('email')
    name = self.request.get('name')
    last_name = self.request.get('lastname')
    webpage = self.request.get('webpage')
    """ Change the fields ................................................................................................"""
    self.user.set_email(email)
    self.user.set_name(name)
    self.user.set_lastname(last_name)
    self.user.put()
    fac = models.Faculty.get_by_id(self.user.auth_ids[0])
    fac.webpage = webpage
    fac.put()
    self.display_message("information saved successfully","faculty")

class FacultyCoursesHandler(BaseHandler):
  @faculty_required
  def get(self):
    self.render_template('faculty/courses.html')

class FacultyRequestsHandler(BaseHandler):
  @faculty_required
  def get(self):
    course_list = list()
    request_type_list = list()
    request_student_list = list()
    request_content_list = list()
    request_course_list = list()
    fac = models.Faculty.get_by_id(self.user.auth_ids[0])
    request_query = models.Application.query(models.Application.faculty==fac.key, models.Application.status==False)
    requests = request_query.fetch(100)
    course_query = models.Course.query(models.Course.coordinator==fac.key)
    courses = course_query.fetch(100)
    for request in requests:
      request_type_list.append(request.app_type)
    stud_query = models.Student.query(models.Student.key==request.student)
    stud = stud_query.fetch(1)
    request_student_list.append(stud[0].name)    ######### why is the username passing on, instead of name???
    request_content_list.append(request.content)
    if request.app_type:
      c_query = models.Course.query(models.Course.key==request.course)
      cou = c_query.fetch(1)
      request_course_list.append(cou[0].course_id)
    else:
      request_course_list.append("")
    c = zip(request_type_list,request_student_list,request_content_list, request_course_list)
    for course in courses:
      course_list.append(course)
      params = {
      'user_data' : self.user,
      'userid' : self.user.auth_ids[0],
      'faculty_data' : models.Faculty.get_by_id(self.user.auth_ids[0]),
      'courses':course_list,
      'requests':c
      }
    logging.info(models.Student.get_by_id(self.user.auth_ids[0]))
    self.render_template('faculty/requests.html',params)
  
  def post(self):
    apptype = self.request.get('type')
    content = self.request.get('content')
    student = self.request.get('student')
    stud = models.Student.get_by_id(student)
    if (apptype=='Approval'):
      coursename = self.request.get('course')
      course = models.Course.get_by_id(coursename)
      app_query = models.Application.query(models.Application.app_type==True, 
                         models.Application.student==stud.key, 
                         models.Application.content==content, 
                         models.Application.course==course.key)
      apps = app_query.fetch(100)
      app = apps[0]
      user_query = models.User.query(models.User.key==stud.student)
      users = user_query.fetch(10)
      user = users[0]
      dep_query = models.Department.query(models.Department.key==user.department)
      deps = dep_query.fetch(10)
      dep = deps[0]
      if (dep.hod==models.Faculty.get_by_id(self.user.auth_ids[0]).key):  # approved by hod
        k=app.put()
        k.delete()
        reg_query = models.Registration.query(models.Registration.student==stud.key, models.Registration.course==course.key)
        regs=reg_query.fetch(10)
        reg=regs[0]
        reg.closed=False
        reg.put()
      else:  # move forward to HOD
        app.faculty=dep.hod
        app.put()
    else:
      app_query = models.Application.query(models.Application.app_type==False, 
                         models.Application.student==stud.key, 
                         models.Application.content==content)
      apps = app_query.fetch(100)
      app = apps[0]
      k=app.put()
      stud.credits = stud.credits + 5.0
      stud.put()
      k.delete()   
    self.display_message("Application approved","faculty")
      
      
