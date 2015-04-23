from misc import *
from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.ext.webapp.util import run_wsgi_app

class AdminHandler(BaseHandler):
  @admin_required
  def get(self):
    reg = models.Registration_status.get_by_id("registration_status")
    reg_status = False
    if reg.open:
      reg_status = True 

    params = {'current_sem':current_sem, 'registration_open':registration_open, 'reg_status':reg_status}
    self.render_template('admin/admin.html',params)

  def post(self):
    logging.info("line 18 called")
    if self.request.POST.get('myform')=="Switch registration":
      stat = self.request.get('reg')
      logging.info(stat)
      reg_entity = models.Registration_status.get_by_id("registration_status")
      if stat == "open":
        reg_entity.open = True
      elif stat == "closed":
        reg_entity.open = False
      reg_entity.put()
      #self.display_popup("registration status changed")
      self.redirect(self.uri_for('admin'))

class AdminInfoHandler(BaseHandler):
  @admin_required
  def get(self):
    self.render_template('admin/info.html')

  def post(self):
    self.render_template('admin/admin.html')



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
      stu = models.Student(student=user.key,name=name+" "+last_name, credits=10, id=user_name)
      stu.put()

    if(role=="faculty"):
      fac = models.Faculty(faculty=user.key,name=name+" "+last_name, id=user_name)
      fac.put()

    user_id = user.get_id()

    token = self.user_model.create_signup_token(user_id)

    verification_url = self.uri_for('verification', type='v', user_id=user_id,
      signup_token=token, _full=True)

    #msg = 'Send an email to user in order to verify their address. \
    #      They will be able to do so by visiting <a href="{url}">{url}</a>'

    #self.display_message(msg.format(url=verification_url))
    self.display_message("user created")

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
      self.display_message("Department created")
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
  	#get a list of all departments
  	dep = models.Department.query()
  	#get a list of all faculties
  	fac = models.Faculty.query()
  	courses = models.Course.query()
  	params = {"dep":dep, "fac":fac, "courses":courses}
  	self.render_template('admin/floatCourse.html',params)

  def post(self):
    logging.info(self.request.POST.get("myform"))
    if self.request.POST.get("myform") == "Update course":
	    course_id = self.request.get('course_id')
	    name = self.request.get('name')
	    dep_id = self.request.get('dep_id')
	    logging.info(dep_id+"this was dep id")
	    description = self.request.get('description')
	    floated = self.request.get('floated')
	    prereq1 = self.request.get('prereq1')
	    prereq2 = self.request.get('prereq2')
	    prereq3 = self.request.get('prereq3')
	    prereq4 = self.request.get('prereq4')
	    prereqs = [prereq1,prereq2,prereq3,prereq4]
	    credits = float(self.request.get('credits'))
	    d = models.Department.get_by_id(dep_id)
	    course = models.Course(course_id=course_id, name=name,
	    	description=description, credits = credits,
	    	department=ndb.Key(urlsafe=dep_id),floated=False,id=course_id
	    	)
	    for i in range(0,4):
	    	p = prereqs[i]
	    	if p!="":
	    		course.prereq.append(ndb.Key(urlsafe=p))
	    course.put()
	    self.display_message("course created successfully")

    elif self.request.POST.get("myform") == "Float the course":
	    course_id = self.request.get('course_id2')
	    logging.info("course id is")
	    logging.info(course_id)
	    faculty_id = self.request.get('faculty_id')
	    logging.info(faculty_id)
	    course = models.Course.get_by_id(ndb.Key(urlsafe=course_id).string_id())
	    course.floated = True
	    course.coordinator = ndb.Key(urlsafe=faculty_id)
	    course.put()
	    self.display_message("course %s (%s) floated" %(course.name,course.course_id))


class resourcesHandler(BaseHandler):
  @admin_required
  def get(self):
  	upload_url = blobstore.create_upload_url('/admin/resource_upload')
  	resources = models.Resources.query()
  	params={"upload_url":upload_url,"resources":resources}
  	self.render_template('admin/resources.html',params)
  	logging.info("upload url = "+upload_url)
  	#upload_url = blobstore.create_upload_url('/admin/upload_photo')
        # [END upload_url]
        # [START upload_form]
        # The method must be "POST" and enctype must be set to "multipart/form-data".
     #   self.response.out.write('<html><body>')
     #  self.response.out.write('<form action="%s" method="POST" enctype="multipart/form-data">' % upload_url)
    #   self.response.out.write('''Upload File: <input type="text" name="resource_id"><br> <input type="file" name="file"><br> <input type="submit"
    #       name="submit" value="Submit"> </form></body></html>''')
     #   logging.info("here1")

class resourceuploadHandler(blobstore_handlers.BlobstoreUploadHandler,BaseHandler):
  def post(self):
    try:
      upload = self.get_uploads()[0]
      logging.info("upload key "+str(upload.key()))
      resource_title = self.request.get('resource_title')
      rr_query = models.Resources.query(models.Resources.resource_title == resource_title)
      rr = rr_query.fetch()
      for r in rr:
        r.key.delete()
      resource = models.Resources(resource_title=resource_title,resource_key=upload.key())
      resource.put()
      #logging.info("here3")
  		#self.redirect('/admin/view_resource/%s' % upload.key())
      self.display_message("Resource uploaded")
    except:
      self.display_message("An error occured, please try again")
		#pass

class viewresourceHandler(blobstore_handlers.BlobstoreDownloadHandler,BaseHandler):
    def post(self):
    	#logging.info("here4")
        #logging.info("key is "+photo_key)
        rid = self.request.get('title')
        logging.info("rid = ")
        logging.info(ndb.Key(urlsafe=rid).integer_id())
        resource = models.Resources.get_by_id(ndb.Key(urlsafe=rid).integer_id())
        bi = blobstore.BlobInfo.get(resource.resource_key)
        self.send_blob(bi,save_as=True)
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

class toggleregistrationHandler(BaseHandler):
  @admin_required
  def get(self):
    reg = models.Registration_status.get_by_id("registration_status")
    reg_status = False
    if reg.open:
      reg_status = True 

    params = {'current_sem':current_sem, 'registration_open':registration_open, 'reg_status':reg_status}
    self.render_template('admin/toggle_registration.html',params)

  def post(self):
      stat = self.request.get('reg')
      logging.info(stat)
      reg_entity = models.Registration_status.get_by_id("registration_status")
      if stat == "open":
        reg_entity.open = True
      elif stat == "closed":
        reg_entity.open = False
      reg_entity.put()
      #self.display_popup("registration status changed")
      params = {"message":"registration status toggled","link":"/admin/toggle_registration"}
      self.display_popup(params);
