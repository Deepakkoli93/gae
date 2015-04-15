from misc import *
class AdminHandler(BaseHandler):
  @user_required
  def get(self):
    params = {'current_sem':current_sem, 'registration_open':registration_open}
    self.render_template('admin/admin.html',params)
  def post(self):
    if(self.request.POST.get('newsem') == "Start new semester"):
      current_sem = current_sem + 1
      self.display_message("new semester started")

class SignupHandler(BaseHandler):
  @admin_required
  def get(self):
    self.render_template('admin/signup.html')

  def post(self):
    user_name = self.request.get('username')
    email = self.request.get('email')
    name = self.request.get('name')
    password = self.request.get('password')
    last_name = self.request.get('lastname')
    department = self.request.get('department')
    role = self.request.get('role')
    #logging.info('role of the student is %s' %role)

    if role=="admin":
      user_data=self.user_model.create_user(user_name,
      email_address=email, name=name, password_raw=password,
      last_name=last_name, role=role,verified=True)
      if not user_data[0]: #user_data is a tuple
        self.display_message('Unable to create user for email %s because of \
        duplicate keys %s' % (user_name, user_data[1]))
      return
    
      user = user_data[1]
      user_id = user.get_id()

      token = self.user_model.create_signup_token(user_id)

      verification_url = self.uri_for('verification', type='v', user_id=user_id,
      signup_token=token, _full=True)

      msg = 'Send an email to user in order to verify their address. \
          They will be able to do so by visiting <a href="{url}">{url}</a>'

      self.display_message(msg.format(url=verification_url))
      return
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
      stu = models.Student(student=user.key, credits=10, id=user_name)
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

class addDepartmentHandler(BaseHandler):
  @admin_required
  def get(self):
    self.render_template('admin/addDepartment.html')

  def post(self):
    dep_id = self.request.get('dep_id')
    name = self.request.get('name')
    hod = self.request.get('hod')
    if hod == "": #creating a new dept without a hod
      dep = models.Department(dep_id=dep_id, name=name, id=dep_id)
      dep.put()
      return
    else:
      valid_hod  = models.Faculty.get_by_id(hod)
      dep = models.Department.get_by_id(dep_id)
      if valid_hod==None:
        self.display_message("hod does not exist")
      else:
        if dep==None:
          dep = self.models.Department(dep_id=dep_id, name=name, hod=valid_hod.key, id=dep_id)
          dep.put()
          self.display_message("info edited successfully")
        else:
          dep.name = name
          dep.hod = valid_hod.key
          dep.put()
          self.display_message("info edited successfully")

class floatCourseHandler(BaseHandler):
  @admin_required
  def get(self):
    self.render_template('admin/floatCourse.html')

  def post(self):
    course_id = self.request.get('course_id')
    name = self.request.get('name')
    coordinator = self.request.get('coordinator')
    department = self.request.get('department')
    floated = self.request.get('floated')
    prereq = self.request.get('prereq')

class resourcesHandler(BaseHandler):
  @admin_required
  def get(self):
    self.render_template('admin/resources.html')

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