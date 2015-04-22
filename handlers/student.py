from misc import *
from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.ext.webapp.util import run_wsgi_app

class StudentHandler(BaseHandler):
  @user_required
  def get(self):
	course_list =list()
	stud = models.Student.get_by_id(self.user.auth_ids[0])
	reg_query = models.Registration.query(models.Registration.student==stud.key)
	regs = reg_query.fetch(10)
	for registration in regs:
		c_query = models.Course.query(models.Course.key==registration.course)
		courses = c_query.fetch(1)
		course = courses[0]
		course_list.append(course)
	params = {'courses':course_list}
	self.render_template('student/student.html',params)
	
  def post(self): # only called if you press one of the course buttons
	course_list = list()
    	stud = models.Student.get_by_id(self.user.auth_ids[0])
    	reg_query = models.Registration.query(models.Registration.student==stud.key)
    	regs = reg_query.fetch(10)
    	for registration in regs:
		c_query = models.Course.query(models.Course.key==registration.course)
		courses = c_query.fetch(1)
		course = courses[0]
		course_list.append(course)
    	for course in course_list:
		pressed = self.request.get(course.course_id)
		if pressed:
			self.session["CID"] = course.course_id
			#upload_url = blobstore.create_upload_url('/student/resource_upload')
			resources = models.Resources.query(models.Fac_Resources.course==course.key)
			params = {'courses':course_list, "resources":resources}
			self.redirect(self.uri_for('stu_courses'), abort=False)
    
class StudentInfoHandler(BaseHandler):
  @user_required
  def get(self):
	course_list =list()
	stud = models.Student.get_by_id(self.user.auth_ids[0])
	reg_query = models.Registration.query(models.Registration.student==stud.key)
	regs = reg_query.fetch(10)
	for registration in regs:
		c_query = models.Course.query(models.Course.key==registration.course)
		courses = c_query.fetch(1)
		course = courses[0]
		course_list.append(course)
    	params = {
    	'user_data' : self.user,
    	'userid' : self.user.auth_ids[0],
    	'student_data' : models.Student.get_by_id(self.user.auth_ids[0]),
    	'courses':course_list
    	}
    	logging.info(models.Student.get_by_id(self.user.auth_ids[0]))
    	self.render_template('student/info.html', params)
    
  def post(self):
    email = self.request.get('email')
    name = self.request.get('name')
    last_name = self.request.get('lastname')
    self.user.set_email(email)
    self.user.set_name(name)
    self.user.set_lastname(last_name)
    self.user.put()
    self.display_message("information saved successfully","student")

class StudentCoursesHandler(blobstore_handlers.BlobstoreDownloadHandler, BaseHandler):
  @user_required
  def get(self):
	courseid=self.session.get('CID')
	course = models.Course.get_by_id(courseid)
	upload_url = blobstore.create_upload_url('/student/resource_upload')
	course_list =list()
	stud = models.Student.get_by_id(self.user.auth_ids[0])
	reg_query = models.Registration.query(models.Registration.student==stud.key)
	regs = reg_query.fetch(10)
	for registration in regs:
		c_query = models.Course.query(models.Course.key==registration.course)
		courses = c_query.fetch(1)
		course = courses[0]
		course_list.append(course)
	res_query = models.Fac_Resources.query(models.Fac_Resources.course==course.key)
	resources = res_query.fetch(500)
	params = {'courseid':courseid,'courses':course_list, 'resources':resources, "upload_url":upload_url,  'user_data' : self.user, 'userid' : self.user.auth_ids[0], 'faculty_data' : models.Faculty.get_by_id(self.user.auth_ids[0])}
	self.render_template('student/courses.html',params)
	
  def post(self):
	  courseid = self.session.get('CID')
	  course = models.Course.get_by_id(courseid)
	  download = self.request.get('download')
	  if download:
		  rid = self.request.get('link')
		  resource = models.Fac_Resources.get_by_id(ndb.Key(urlsafe=rid).integer_id())
		  bi = blobstore.BlobInfo.get(resource.resource_key)
		  self.send_blob(bi,save_as=True)
		  

class stuResourceuploadHandler(blobstore_handlers.BlobstoreUploadHandler,BaseHandler):
	def post(self):
		#~ logging.info("here2")
		upload = self.get_uploads()[0]
		#~ logging.info("upload key "+str(upload.key()))
		rid = self.request.get('link')
		resource = models.Fac_Resources.get_by_id(ndb.Key(urlsafe=rid).integer_id())
		#~ logging.info(resc_type)
		submission = models.Assignment(student=models.Student.get_by_id(self.user.auth_ids[0]).key, resource_id=resource.key, resource_key=upload.key() )
		submission.put()
		#~ logging.info("here3")
		#self.redirect('/admin/view_resource/%s' % upload.key())
		self.display_message("Submission uploaded","student")

class CartHandler(BaseHandler):
  @user_required
  def get(self):
	course_list =list()
	stud = models.Student.get_by_id(self.user.auth_ids[0])
	reg_query = models.Registration.query(models.Registration.student==stud.key)
	regs = reg_query.fetch(10)
	params = {}
	closed_list = list()
	course_id_list = list()
	course_credits_list = list()
	course_fac_list = list()
	all_courses = models.Course.query(models.Course.floated==True)
	for registration in regs:
		c_query = models.Course.query(models.Course.key==registration.course)
		courses = c_query.fetch(1)
		course = courses[0]
		course_list.append(course)
		course_id_list.append(course.course_id)
		course_credits_list.append(course.credits)
		coordi_query = models.Faculty.query(models.Faculty.key==course.coordinator)
		coordis = coordi_query.fetch(1)
		course_fac_list.append(coordis[0].name)
		closed_list.append(registration.closed)
	c = zip(course_id_list,course_credits_list,course_fac_list,closed_list)
	reg = models.Registration_status.get_by_id("registration_status").open
	reg_status = "disabled"
	if reg:
		reg_status = ""
	params = {
	'student':stud,
	'c':c,
	'courses':course_list,
	'all_courses':all_courses,
	'reg_status':reg_status
	}
	self.render_template('student/cart.html',params)
	
  def post(self):
	relax = self.request.get('relax')
	registerCourse = self.request.get('registerCourse')
	remove = self.request.get('remove')
	approve = self.request.get('approve')
	if relax: # done
		content = self.request.get('relaxation')
		user = self.user
		dep = models.Department.get_by_id(user.department)
		stud = models.Student.get_by_id(self.user.auth_ids[0])
		#hod = models.Faculty.get_by_id(dep.hod.string_id())
		app_query = models.Application.query(models.Application.app_type==False, models.Application.student==stud.key, models.Application.faculty==dep.hod).fetch(1)
		if not app_query:
			app = models.Application(app_type=False,student=stud.key,faculty=dep.hod,content=content,status=False)
			app.put()
			params = {"message":"your application has been forwarded to the hod", "link":"/student/cart"}
			self.display_popup(params)
		else:
			params = {"message":"you have already placed an application", "link":"/student/cart"}
			self.display_popup(params)

	elif registerCourse:  # done
		coursename = self.request.get('course')
		course = models.Course.get_by_id(ndb.Key(urlsafe=coursename).string_id())
		logging.info(course)
		if course==None:
			self.display_message("course is empty","student")
		else:
			user = self.user
			stud = models.Student.get_by_id(self.user.auth_ids[0])
			query_res = models.Registration.query(models.Registration.course==course.key)
			listed = query_res.fetch(100)
			count = listed.__len__()
			logging.info(str(stud.credits) + " "+str(course.credits))
			if course.floated:
				if (stud.credits>=course.credits):
					reg_query = models.Registration.query(models.Registration.course==course.key, models.Registration.student==stud.key)
					#logging.info(reg)
					reg_query_res = reg_query.fetch()
					logging.info(reg_query_res)
					if reg_query_res == []:
						reg = models.Registration(course=course.key,student=stud.key,closed=(count>=10))
						reg.put()
						stud.credits = stud.credits - course.credits
						stud.put()
						params = {"message":"course added to your cart","link":'/student/cart'}
						self.display_popup(params)
						#return
					else:
						params = {"message":"you have already added this course","link":'/student/cart'}
						self.display_popup(params)
						#return
				else:
					params = {"message":"credit limit exceeded, try removing a course","link":'/student/cart'}
					self.display_popup(params)
					#return
			else:
				self.display_message("course is not floated","student")
	elif remove: # done
		courseid = self.request.get('course_id')
		course = models.Course.get_by_id(courseid)
		stud = models.Student.get_by_id(self.user.auth_ids[0])
		stud.credits = stud.credits + course.credits
		stud.put()
		reg_query = models.Registration.query(models.Registration.student==stud.key,models.Registration.course==course.key)
		reg = reg_query.get()
		reg.key.delete()
		params = {"message":"course removed", "link":'/student/cart'}
		self.display_popup(params)
	else: # done
		courseid = self.request.get('course_id')
		logging.info(courseid)
		course = models.Course.get_by_id(courseid)
		content = self.request.get('approval')
		if content == "":
			content = "Kindly approve the course"
		stud = models.Student.get_by_id(self.user.auth_ids[0])
		#facs = models.Faculty.get_by_id(course.coordinator.string_id())
		#facs = fac_query.fetch(1)
		app_query =  models.Application.query(models.Application.app_type==True,models.Application.student==stud.key,models.Application.course==course.key,models.Application.faculty==course.coordinator).fetch(1)
		if not app_query:
			app = models.Application(app_type=True,student=stud.key,course=course.key,faculty=course.coordinator,content=content,status=False)
			app.put()
			params = {"message":"application forwarded", "link":'/student/cart'}
			self.display_popup(params)
		else:
			params = {"message":"you have already requested approval","link":'/student/cart'}
			self.display_popup(params)
	#self.redirect(self.uri_for('cart'))
	course_list =list()
	stud = models.Student.get_by_id(self.user.auth_ids[0])
	reg_query = models.Registration.query(models.Registration.student==stud.key)
	regs = reg_query.fetch(10)
	for registration in regs:
		c_query = models.Course.query(models.Course.key==registration.course)
		courses = c_query.fetch(1)
		course = courses[0]
		course_list.append(course)
	params = {'courses':course_list}
	#self.render_template('student/student.html',params)
		#self.redirect(self.uri_for('student'))

class studentresourcesHandler(BaseHandler):
	@user_required
	def get(self):
		course_list =list()
		stud = models.Student.get_by_id(self.user.auth_ids[0])
		reg_query = models.Registration.query(models.Registration.student==stud.key)
		regs = reg_query.fetch(10)
		resources = models.Resources.query()
		for registration in regs:
			c_query = models.Course.query(models.Course.key==registration.course)
			courses = c_query.fetch(1)
			course = courses[0]
			course_list.append(course)
		params = {
		'user_data' : self.user,
		'userid' : self.user.auth_ids[0],
		'student_data' : models.Student.get_by_id(self.user.auth_ids[0]),
		'courses':course_list,
		'resources':resources
		}
		logging.info(models.Student.get_by_id(self.user.auth_ids[0]))
		self.render_template('student/resources.html', params)
