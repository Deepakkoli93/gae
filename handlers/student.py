from misc import *
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
			params = {'course':course,'courses':course_list}
			self.render_template('student/courses.html',params)
    
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

class StudentCoursesHandler(BaseHandler):
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
	self.render_template('student/courses.html',params)

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
	params = {
	'student':stud,
	'c':c,
	'courses':course_list
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
        	hod_query = models.Faculty.query(models.Faculty.key==dep.hod)
		hods = hod_query.fetch(1)
        	app = models.Application(app_type=False,student=stud.key,faculty=hods[0].key,content=content,status=False)
        	app.put()
        	pass
        elif registerCourse:  # done
		coursename = self.request.get('course')
		course = models.Course.get_by_id(coursename)
		if course==None:
			self.display_message("course is empty","student")
		else:
		    	user = self.user
			stud = models.Student.get_by_id(self.user.auth_ids[0])
			query_res = models.Registration.query(models.Registration.course==course.key)
			listed = query_res.fetch(100)
			count = listed.__len__()
			if course.floated:
				if (stud.credits>=course.credits):
					reg = models.Registration(course=course.key,student=stud.key,closed=(count>=10))
					reg.put()
					stud.credits = stud.credits - course.credits
					stud.put()
	elif remove: # done
		courseid = self.request.get('course_id')
		course = models.Course.get_by_id(courseid)
		stud = models.Student.get_by_id(self.user.auth_ids[0])
		stud.credits = stud.credits + course.credits
		stud.put()
		reg_query = models.Registration.query(models.Registration.student==stud.key,models.Registration.course==course.key)
		reg = reg_query.get()
		reg.key.delete()
	else: # done
		courseid = self.request.get('course_id')
		course = models.Course.get_by_id(courseid)
        	stud = models.Student.get_by_id(self.user.auth_ids[0])
        	fac_query = models.Faculty.query(models.Faculty.key==course.coordinator)
		facs = fac_query.fetch(1)
        	app = models.Application(app_type=True,student=stud.key,faculty=facs[0].key,content=content,status=False)
        	app.put()
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
