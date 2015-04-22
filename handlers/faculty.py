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
		#~ logging.info(models.Faculty.get_by_id(self.user.auth_ids[0]))
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
			if pressed:
				upload_url = blobstore.create_upload_url('/faculty/resource_upload')
				resources = models.Resources.query(models.Fac_Resources.course==course.key)
				self.session['CID'] = course.course_id
				logging.info("line 37 cookie set!!")
				logging.info(self.session.get('CID'))
				#~ logging.info(self.session.get('CID'))
				#~ self.request.headers['Cookie'] = 'Cid='+course.course_id
				#~ logging.info('Cid='+course.course_id)
				#~ self.response.set_cookie('course',course.course_id,overwrite=True)
				params = {'courses':course_list,"upload_url":upload_url,"resources":resources}
				#~ self.render_template('faculty/courses.html',params)
				self.redirect(self.uri_for('fac_courses'))

class FacultyInfoHandler(BaseHandler):
  @faculty_required
  def get(self):
  	logging.info("faculty info")
  	logging.info(self.session)
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

class FacultyCoursesHandler(blobstore_handlers.BlobstoreDownloadHandler, BaseHandler):
  @faculty_required
  def get(self):
  	  logging.info("check this")
	  courseid=self.session.get('CID')
	  logging.info(self.session)
	  course = models.Course.get_by_id(courseid)
	  upload_url = blobstore.create_upload_url('/faculty/resource_upload')
	  logging.info("upload url = "+upload_url)
	  #~ logging.info(self.session.get('CID'))
	  course_list =list()
	  resource_type_list=list()
	  resource_title_list=list()
	  resource_link_list=list()
	  fac = models.Faculty.get_by_id(self.user.auth_ids[0])
	  course_query = models.Course.query(models.Course.coordinator==fac.key)
	  courses = course_query.fetch(100)
	  for cse in courses:
		course_list.append(cse)
	  res_query=models.Fac_Resources.query(models.Fac_Resources.course==course.key)
	  resources = res_query.fetch(500)
	  #for resource in resources:
		#resource_type_list.append(resource.resource_type)
		#resource_title_list.append(resource.resource_title)
		#resource_link_list.append(resource.key.urlsafe)
		#logging.info(resource.key.urlsafe)
	  #c=zip(resource_type_list, resource_title_list, resource_link_list)
	  params = {'courseid':courseid, 'resources':resources, "upload_url":upload_url, 'user_data' : self.user, 'userid' : self.user.auth_ids[0], 'faculty_data' : models.Faculty.get_by_id(self.user.auth_ids[0]), 'courses':course_list }
	  self.render_template('faculty/courses.html',params)
	  
  def post(self):
	  courseid = self.session.get('CID')
	  course = models.Course.get_by_id(courseid)
	  download = self.request.get('download')
	  view = self.request.get('view')
	  if download:
		  rid = self.request.get('link')
		  logging.info("rid="+rid)
		  resource = models.Fac_Resources.get_by_id(ndb.Key(urlsafe=rid).integer_id())
		  logging.info("check resource")
		  logging.info(resource)
		  bi = blobstore.BlobInfo.get(resource.resource_key)
		  self.send_blob(bi,save_as=True)
		  #self.display_message("Resource downloaded","faculty")
	  else:
		  rid = self.request.get('link')
		  resource = models.Fac_Resources.get_by_id(ndb.Key(urlsafe=rid).integer_id())
		  stud_ids = list()
		  submission_links = list()
		  sub_query = models.Assignment.query(models.Assignment.resource_id==resource.key)
		  subs = sub_query.fetch(500)
		  for sub in subs:
			  stud = models.Student.get_by_id(sub.student)
			  stud_ids.append(stud.name)
			  submission_links.append(str(sub.resource_key))
		  c = zip(stud_ids,submission_links)
		  course_list =list()
		  fac = models.Faculty.get_by_id(self.user.auth_ids[0])
		  course_query = models.Course.query(models.Course.coordinator==fac.key)
		  courses = course_query.fetch(500)
		  for cse in courses:
			  course_list.append(cse)
		  params = {'courseid':courseid, 'c':c, 'user_data' : self.user, 'userid' : self.user.auth_ids[0], 'faculty_data' : models.Faculty.get_by_id(self.user.auth_ids[0]), 'courses':course_list }
		  self.render_template('faculty/submissions.html',params)
		  
class facResourceuploadHandler(blobstore_handlers.BlobstoreUploadHandler,BaseHandler):
	def post(self):
		#~ logging.info("here2")
		courseid = self.session.get('CID')
		logging.info("self session")
		logging.info(self.session)
		course = models.Course.get_by_id(courseid)
		
		upload = self.get_uploads()[0]
		#~ logging.info("upload key "+str(upload.key()))
		resource_title = self.request.get('resource_title')
		resc_type = self.request.get('res_type')
		logging.info(resc_type)
		if (resc_type=="Assignment"):
			resource_type=True
		else:
			resource_type=False
		resource = models.Fac_Resources(resource_title=resource_title,resource_key=upload.key(),resource_type=resource_type, course=course.key)
		resource.put()
		#~ logging.info("here3")
		#self.redirect('/admin/view_resource/%s' % upload.key())
		self.display_message("Resource uploaded","faculty")
		#pass
		
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
		stud = models.Student.get_by_id(request.student.string_id())
		logging.info(stud)
		request_student_list.append(stud.name)    ######### why is the username passing on, instead of name???
		request_content_list.append(str(request.content))
		if request.app_type:
			logging.info(request.course==None)
			cou = models.Course.get_by_id(request.course.string_id())
			logging.info(cou)
			#cou = c_query.fetch(1)
			request_course_list.append(cou.course_id)
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
		#logging.info(models.Student.get_by_id(self.user.auth_ids[0]))
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
		  dep_query = models.Department.query(models.Department.key==ndb.Key("Department",user.department))
		  deps = dep_query.fetch(10)
		  dep = deps[0]
		  if (dep.hod==models.Faculty.get_by_id(self.user.auth_ids[0]).key):  # approved by hod
			  k=app.put()
			  k.delete()
			  reg_query = models.Registration.query(models.Registration.student==stud.key, models.Registration.course==course.key)
			  regs=reg_query.fetch(10)
			  if not regs:
			  	params = {"message":"looks like the student already removed the course","link":'/faculty/requests'}
			  	self.display_popup(params)
			  else:
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
		  
		  
