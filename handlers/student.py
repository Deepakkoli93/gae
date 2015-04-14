from misc import *
class StudentHandler(BaseHandler):
  @user_required
  def get(self):
    self.render_template('student/student.html')

class StudentInfoHandler(BaseHandler):
  @user_required
  def get(self):
    params = {
    'user_data' : self.user,
    'student_data' : models.Student.get_by_id(self.user.auth_ids[0])
    }
    self.render_template('student/info.html', params)

class CartHandler(BaseHandler):
  @user_required
  def get(self):
    self.render_template('student/cart.html')